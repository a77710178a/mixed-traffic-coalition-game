from __future__ import annotations

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


def _lane_center(approach: str, distance_from_center: float, lane_width: float) -> tuple[float, float]:
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
    end = _lane_center(destination, approach_length, lane_width)

    if movement == "through":
        return [start, end]

    entry = _lane_center(origin, turn_radius, lane_width)
    exit_ = _lane_center(destination, turn_radius, lane_width)
    control = _route_control_point(movement, turn_radius)
    curve_steps = max(6, int(math.ceil(math.pi * turn_radius / max(0.5, float(cfg["path_sample_interval_m"])))))
    curve = [_quadratic(entry, control, exit_, index / curve_steps) for index in range(curve_steps + 1)]
    return [start, entry, *curve[1:-1], exit_, end]


def _control_region_path(path: list[dict[str, float]], max_distance: float) -> list[dict[str, float]]:
    return [
        point
        for point in path
        if math.hypot(point["x"], point["y"]) <= max_distance
    ]


def _minimum_distance(path_a: list[dict[str, float]], path_b: list[dict[str, float]]) -> tuple[float, tuple[float, float]]:
    minimum = float("inf")
    midpoint = (0.0, 0.0)
    for point_a in path_a:
        for point_b in path_b:
            distance = math.hypot(point_a["x"] - point_b["x"], point_a["y"] - point_b["y"])
            if distance < minimum:
                minimum = distance
                midpoint = ((point_a["x"] + point_b["x"]) / 2.0, (point_a["y"] + point_b["y"]) / 2.0)
    return minimum, midpoint


def _routes_conflict(route_a: dict, route_b: dict, cfg: dict) -> tuple[bool, tuple[float, float] | None]:
    if route_a["origin"] == route_b["origin"]:
        return False, None
    if route_a["movement"] == "through" and route_b["movement"] == "through":
        return False, None

    max_distance = float(cfg["control_region_distance_m"])
    path_a = _control_region_path(route_a["path"], max_distance)
    path_b = _control_region_path(route_b["path"], max_distance)
    if not path_a or not path_b:
        return False, None

    width = float(cfg["vehicle_dimensions_m"]["width"])
    buffer = float(cfg["geometry_safety_buffer_m"])
    tolerance = float(cfg["static_overlap_tolerance_m2"])
    threshold = width + buffer + tolerance
    minimum, midpoint = _minimum_distance(path_a, path_b)
    return minimum <= threshold, midpoint


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
            "origin": spec.origin,
            "destination": spec.destination,
            "movement": spec.movement,
            "path": _sample_polyline(points, float(cfg["path_sample_interval_m"])),
        }

    matrix = {route_id: {other_id: False for other_id in routes} for route_id in routes}
    zones = {}
    route_ids = [route_id for route_id in LEGAL_T_JUNCTION_ROUTE_ORDER if route_id in routes]
    for left_index, route_a_id in enumerate(route_ids):
        for route_b_id in route_ids[left_index + 1:]:
            conflicts, center = _routes_conflict(routes[route_a_id], routes[route_b_id], cfg)
            matrix[route_a_id][route_b_id] = conflicts
            matrix[route_b_id][route_a_id] = conflicts
            if conflicts and center is not None:
                zone_id = f"{route_a_id}__{route_b_id}"
                zones[zone_id] = {
                    "route_a": route_a_id,
                    "route_b": route_b_id,
                    "center": {"x": _round(center[0]), "y": _round(center[1])},
                    "radius_m": _round(float(cfg["vehicle_dimensions_m"]["width"]) + float(cfg["geometry_safety_buffer_m"])),
                }

    return {
        "scenario_name": cfg.get("scenario_name", ""),
        "geometry_mode": cfg.get("geometry_mode", "lane_offset_paths"),
        "lane_width_m": float(cfg["lane_width_m"]),
        "turn_radius_m": float(cfg["turn_radius_m"]),
        "vehicle_dimensions_m": cfg["vehicle_dimensions_m"],
        "geometry_safety_buffer_m": float(cfg["geometry_safety_buffer_m"]),
        "control_region_distance_m": float(cfg["control_region_distance_m"]),
        "path_sample_interval_m": float(cfg["path_sample_interval_m"]),
        "static_overlap_tolerance_m2": float(cfg["static_overlap_tolerance_m2"]),
        "routes": routes,
        "conflict_matrix": matrix,
        "conflict_zones": zones,
    }


def write_route_geometry(cfg: dict, path: str | Path | None = None) -> Path:
    output_path = Path(path) if path is not None else geometry_artifact_path(cfg)
    write_json(output_path, build_route_geometry(cfg))
    return output_path
