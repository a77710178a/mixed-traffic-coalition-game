from __future__ import annotations

import json
import math
from pathlib import Path

from common import geometry_artifact_path, write_json
from topology import active_approaches, route_specs


LEGAL_T_JUNCTION_ROUTES = {
    "r_N_through",
    "r_N_left",
    "r_S_through",
    "r_S_right",
    "r_E_right",
    "r_E_left",
}
LEGAL_T_JUNCTION_ROUTE_ORDER = (
    "r_N_through",
    "r_N_left",
    "r_S_through",
    "r_S_right",
    "r_E_right",
    "r_E_left",
)

APPROACH_VECTOR = {
    "N": (0.0, -1.0),
    "E": (-1.0, 0.0),
    "S": (0.0, 1.0),
    "W": (1.0, 0.0),
}


def _round(value: float) -> float:
    return round(float(value), 3)


def _add(point: tuple[float, float], vector: tuple[float, float], scale: float) -> tuple[float, float]:
    return point[0] + vector[0] * scale, point[1] + vector[1] * scale


def _left_normal(vector: tuple[float, float]) -> tuple[float, float]:
    return -vector[1], vector[0]


def _right_normal(vector: tuple[float, float]) -> tuple[float, float]:
    return vector[1], -vector[0]


def _lane_center(approach: str, distance_from_center: float, lane_width: float) -> tuple[float, float]:
    inbound = APPROACH_VECTOR[approach]
    offset = lane_width / 2.0
    return _add((-inbound[0] * distance_from_center, -inbound[1] * distance_from_center), _right_normal(inbound), offset)


def _outgoing_lane_center(approach: str, distance_from_center: float, lane_width: float) -> tuple[float, float]:
    inbound = APPROACH_VECTOR[approach]
    offset = lane_width / 2.0
    return _add((-inbound[0] * distance_from_center, -inbound[1] * distance_from_center), _left_normal(inbound), offset)


def _quadratic(
    start: tuple[float, float],
    control: tuple[float, float],
    end: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    inv = 1.0 - t
    x = inv * inv * start[0] + 2.0 * inv * t * control[0] + t * t * end[0]
    y = inv * inv * start[1] + 2.0 * inv * t * control[1] + t * t * end[1]
    return x, y


def _polyline_length(points: list[tuple[float, float]]) -> float:
    return sum(
        math.hypot(points[index + 1][0] - points[index][0], points[index + 1][1] - points[index][1])
        for index in range(len(points) - 1)
    )


def _polyline_points_with_distance(points: list[tuple[float, float]]) -> list[tuple[float, float, float]]:
    output = []
    distance = 0.0
    for index, point in enumerate(points):
        if index > 0:
            previous = points[index - 1]
            distance += math.hypot(point[0] - previous[0], point[1] - previous[1])
        output.append((point[0], point[1], distance))
    return output


def _sample_polyline(points: list[tuple[float, float]], interval: float) -> list[dict[str, float]]:
    if len(points) < 2:
        raise ValueError("At least two path points are required")
    interval = max(0.1, float(interval))
    total = _polyline_length(points)
    targets = [index * interval for index in range(int(total // interval) + 1)]
    if not math.isclose(targets[-1], total):
        targets.append(total)

    samples = []
    segment_index = 0
    distance_before_segment = 0.0
    for target in targets:
        while segment_index < len(points) - 2:
            start = points[segment_index]
            end = points[segment_index + 1]
            segment_length = math.hypot(end[0] - start[0], end[1] - start[1])
            if distance_before_segment + segment_length >= target:
                break
            distance_before_segment += segment_length
            segment_index += 1

        start = points[segment_index]
        end = points[segment_index + 1]
        segment_length = math.hypot(end[0] - start[0], end[1] - start[1])
        ratio = 0.0 if segment_length == 0.0 else (target - distance_before_segment) / segment_length
        x = start[0] + (end[0] - start[0]) * ratio
        y = start[1] + (end[1] - start[1]) * ratio
        samples.append({"s_m": _round(target), "x": _round(x), "y": _round(y)})
    return samples


def _route_control_point(movement: str, turn_radius: float) -> tuple[float, float]:
    if movement == "through":
        return 0.0, 0.0
    return 0.0, 0.0


def _route_points(origin: str, destination: str, movement: str, cfg: dict) -> list[tuple[float, float]]:
    lane_width = float(cfg["lane_width_m"])
    approach_length = float(cfg["approach_length_m"])
    turn_radius = float(cfg["turn_radius_m"])
    start = _lane_center(origin, approach_length, lane_width)
    end = _outgoing_lane_center(destination, approach_length, lane_width)

    if movement == "through":
        return [start, end]

    entry = _lane_center(origin, turn_radius, lane_width)
    exit_ = _outgoing_lane_center(destination, turn_radius, lane_width)
    control = _route_control_point(movement, turn_radius)
    curve_steps = max(12, int(math.ceil(math.pi * turn_radius)))
    curve = [_quadratic(entry, control, exit_, index / curve_steps) for index in range(curve_steps + 1)]
    return [start, entry, *curve[1:-1], exit_, end]


def _control_region_segments(points: list[tuple[float, float, float]], max_distance: float) -> list[tuple[tuple[float, float, float], tuple[float, float, float]]]:
    segments = []
    for start, end in zip(points, points[1:]):
        if math.hypot(start[0], start[1]) <= max_distance or math.hypot(end[0], end[1]) <= max_distance:
            segments.append((start, end))
    return segments


def _project_unit_interval(
    point: tuple[float, float],
    start: tuple[float, float, float],
    end: tuple[float, float, float],
) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length_sq = dx * dx + dy * dy
    if length_sq == 0.0:
        return 0.0
    return max(0.0, min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length_sq))


def _interpolate_segment(start: tuple[float, float, float], end: tuple[float, float, float], ratio: float) -> tuple[float, float, float]:
    return (
        start[0] + (end[0] - start[0]) * ratio,
        start[1] + (end[1] - start[1]) * ratio,
        start[2] + (end[2] - start[2]) * ratio,
    )


def _segment_intersection(
    a0: tuple[float, float, float],
    a1: tuple[float, float, float],
    b0: tuple[float, float, float],
    b1: tuple[float, float, float],
) -> tuple[tuple[float, float, float], tuple[float, float, float]] | None:
    ax = a1[0] - a0[0]
    ay = a1[1] - a0[1]
    bx = b1[0] - b0[0]
    by = b1[1] - b0[1]
    denominator = ax * by - ay * bx
    if abs(denominator) < 1e-9:
        return None

    cx = b0[0] - a0[0]
    cy = b0[1] - a0[1]
    ta = (cx * by - cy * bx) / denominator
    tb = (cx * ay - cy * ax) / denominator
    if -1e-9 <= ta <= 1.0 + 1e-9 and -1e-9 <= tb <= 1.0 + 1e-9:
        return _interpolate_segment(a0, a1, max(0.0, min(1.0, ta))), _interpolate_segment(b0, b1, max(0.0, min(1.0, tb)))
    return None


def _point_distance_to_segment(
    point: tuple[float, float, float],
    start: tuple[float, float, float],
    end: tuple[float, float, float],
) -> tuple[float, tuple[float, float, float], tuple[float, float, float]]:
    ratio = _project_unit_interval((point[0], point[1]), start, end)
    projected = _interpolate_segment(start, end, ratio)
    distance = math.hypot(point[0] - projected[0], point[1] - projected[1])
    return distance, point, projected


def _segment_distance(
    a0: tuple[float, float, float],
    a1: tuple[float, float, float],
    b0: tuple[float, float, float],
    b1: tuple[float, float, float],
) -> tuple[float, tuple[float, float, float], tuple[float, float, float]]:
    intersection = _segment_intersection(a0, a1, b0, b1)
    if intersection is not None:
        return 0.0, intersection[0], intersection[1]

    candidates = [
        _point_distance_to_segment(a0, b0, b1),
        _point_distance_to_segment(a1, b0, b1),
        _point_distance_to_segment(b0, a0, a1),
        _point_distance_to_segment(b1, a0, a1),
    ]
    distance, first, second = min(candidates, key=lambda item: item[0])
    if first in {b0, b1}:
        return distance, second, first
    return distance, first, second


def _minimum_segment_distance(
    segments_a: list[tuple[tuple[float, float, float], tuple[float, float, float]]],
    segments_b: list[tuple[tuple[float, float, float], tuple[float, float, float]]],
) -> tuple[float, tuple[float, float], float, float]:
    minimum = float("inf")
    midpoint = (0.0, 0.0)
    s_a = 0.0
    s_b = 0.0
    for start_a, end_a in segments_a:
        for start_b, end_b in segments_b:
            distance, point_a, point_b = _segment_distance(start_a, end_a, start_b, end_b)
            if distance < minimum:
                minimum = distance
                midpoint = ((point_a[0] + point_b[0]) / 2.0, (point_a[1] + point_b[1]) / 2.0)
                s_a = point_a[2]
                s_b = point_b[2]
    return minimum, midpoint, s_a, s_b


def _empty_relation() -> dict:
    return {"conflicts": False, "conflict_type": "none", "zone_ids": []}


def _conflict_type(route_a: dict, route_b: dict) -> str:
    if route_a["origin"] == route_b["origin"]:
        return "diverging" if route_a["destination"] != route_b["destination"] else "queue_following"
    if route_a["destination"] == route_b["destination"]:
        return "merging"
    if route_a["movement"] != "through" and route_b["movement"] != "through":
        return "overlap_turning"
    return "crossing"


def _same_origin_zone(route_a: dict, route_b: dict, cfg: dict) -> tuple[tuple[float, float], float, float]:
    distance = min(float(cfg["control_region_distance_m"]), float(cfg["turn_radius_m"]) * 1.5)
    lane_width = float(cfg["lane_width_m"])
    center = _lane_center(route_a["origin"], distance, lane_width)
    s_a = max(0.0, float(cfg["approach_length_m"]) - distance)
    return center, s_a, s_a


def _relation_for_routes(route_a: dict, route_b: dict, cfg: dict) -> tuple[dict, dict | None]:
    if route_a["movement"] == "through" and route_b["movement"] == "through":
        return _empty_relation(), None

    conflict_type = _conflict_type(route_a, route_b)
    zone_id = f'{route_a["route_id"]}__{route_b["route_id"]}'
    if route_a["origin"] == route_b["origin"]:
        centroid, s_a, s_b = _same_origin_zone(route_a, route_b, cfg)
        zone = _zone(zone_id, route_a["route_id"], route_b["route_id"], conflict_type, centroid, s_a, s_b, cfg)
        return {"conflicts": True, "conflict_type": conflict_type, "zone_ids": [zone_id]}, zone

    max_distance = float(cfg["control_region_distance_m"])
    segments_a = _control_region_segments(route_a["_geometry_points"], max_distance)
    segments_b = _control_region_segments(route_b["_geometry_points"], max_distance)
    if not segments_a or not segments_b:
        return _empty_relation(), None

    width = float(cfg["vehicle_dimensions_m"]["width"])
    buffer = float(cfg["geometry_safety_buffer_m"])
    threshold = 2.0 * (width / 2.0 + buffer)
    minimum, centroid, s_a, s_b = _minimum_segment_distance(segments_a, segments_b)
    if minimum > threshold:
        return _empty_relation(), None

    zone = _zone(zone_id, route_a["route_id"], route_b["route_id"], conflict_type, centroid, s_a, s_b, cfg)
    return {"conflicts": True, "conflict_type": conflict_type, "zone_ids": [zone_id]}, zone


def _zone(
    zone_id: str,
    route_a_id: str,
    route_b_id: str,
    conflict_type: str,
    centroid: tuple[float, float],
    s_a: float,
    s_b: float,
    cfg: dict,
) -> dict:
    radius = float(cfg["vehicle_dimensions_m"]["width"]) / 2.0 + float(cfg["geometry_safety_buffer_m"])
    return {
        "zone_id": zone_id,
        "route_ids": [route_a_id, route_b_id],
        "conflict_type": conflict_type,
        "centroid": {"x": _round(centroid[0]), "y": _round(centroid[1])},
        "radius_m": _round(radius),
        "entry_distance_by_route": {route_a_id: _round(max(0.0, s_a - radius)), route_b_id: _round(max(0.0, s_b - radius))},
        "exit_distance_by_route": {route_a_id: _round(s_a + radius), route_b_id: _round(s_b + radius)},
    }


def build_route_geometry(cfg: dict) -> dict:
    approaches = active_approaches(cfg)
    if set(approaches) != {"N", "E", "S"}:
        raise ValueError("T-junction route geometry currently supports active approaches N, E, and S only")

    routes = {}
    for spec in route_specs(approaches):
        if spec.route_id not in LEGAL_T_JUNCTION_ROUTES:
            continue
        points = _route_points(spec.origin, spec.destination, spec.movement, cfg)
        routes[spec.route_id] = {
            "route_id": spec.route_id,
            "origin": spec.origin,
            "destination": spec.destination,
            "movement": spec.movement,
            "path": _sample_polyline(points, float(cfg["path_sample_interval_m"])),
            "_geometry_points": _polyline_points_with_distance(points),
        }

    matrix = {route_id: {other_id: _empty_relation() for other_id in routes} for route_id in routes}
    zones = []
    route_ids = [route_id for route_id in LEGAL_T_JUNCTION_ROUTE_ORDER if route_id in routes]
    for left_index, route_a_id in enumerate(route_ids):
        for route_b_id in route_ids[left_index + 1:]:
            relation, zone = _relation_for_routes(routes[route_a_id], routes[route_b_id], cfg)
            matrix[route_a_id][route_b_id] = relation
            matrix[route_b_id][route_a_id] = relation
            if zone is not None:
                zones.append(zone)

    conflict_zones = {
        zone["zone_id"]: {
            "route_a": zone["route_ids"][0],
            "route_b": zone["route_ids"][1],
            "center": zone["centroid"],
            "radius_m": zone["radius_m"],
        }
        for zone in zones
    }

    width = float(cfg["vehicle_dimensions_m"]["width"])
    buffer = float(cfg["geometry_safety_buffer_m"])
    serializable_routes = {
        route_id: {key: value for key, value in route.items() if not key.startswith("_")}
        for route_id, route in routes.items()
    }

    return {
        "scenario_name": cfg.get("scenario_name", ""),
        "geometry_mode": cfg.get("geometry_mode", "route_zones"),
        "parameters": {
            "lane_width_m": float(cfg["lane_width_m"]),
            "turn_radius_m": float(cfg["turn_radius_m"]),
            "vehicle_dimensions_m": cfg["vehicle_dimensions_m"],
            "geometry_safety_buffer_m": buffer,
            "control_region_distance_m": float(cfg["control_region_distance_m"]),
            "path_sample_interval_m": float(cfg["path_sample_interval_m"]),
            "static_overlap_tolerance_m2": float(cfg["static_overlap_tolerance_m2"]),
            "overlap_method": "segment_distance_threshold",
            "distance_threshold_m": _round(2.0 * (width / 2.0 + buffer)),
        },
        "routes": serializable_routes,
        "conflict_matrix": matrix,
        "zones": zones,
        "conflict_zones": conflict_zones,
    }


def write_route_geometry(cfg: dict, path: str | Path | None = None) -> Path:
    output_path = Path(path) if path is not None else geometry_artifact_path(cfg)
    write_json(output_path, build_route_geometry(cfg))
    return output_path


def load_route_geometry(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
