from __future__ import annotations

import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from common import movement_to_destination  # noqa: E402
from route_geometry import build_route_geometry  # noqa: E402
from extract_conflict_events import extract_route_zone_events_from_rows  # noqa: E402


def cfg() -> dict:
    return {
        "scenario_name": "t_junction_unsignalized_test",
        "intersection_type": "t_junction",
        "active_approaches": ["N", "E", "S"],
        "approach_length_m": 120.0,
        "lane_width_m": 3.5,
        "turn_radius_m": 10.0,
        "vehicle_dimensions_m": {"length": 4.5, "width": 1.8},
        "geometry_safety_buffer_m": 0.5,
        "control_region_distance_m": 45.0,
        "path_sample_interval_m": 0.25,
        "static_overlap_tolerance_m2": 0.25,
        "geometry_mode": "route_zones",
    }


def row(time: float, veh_id: str, route_id: str, x: float, y: float, speed: float = 5.0, accel: float = 0.0) -> dict:
    origin = route_id.split("_")[1]
    movement = route_id.split("_")[2]
    destination = movement_to_destination(origin, movement)
    return {
        "time": f"{time:.1f}",
        "veh_id": veh_id,
        "veh_class": "HDV" if veh_id.startswith("h") else "CAV",
        "veh_type": "HDV" if veh_id.startswith("h") else "CAV",
        "route_id": route_id,
        "origin": origin,
        "destination": destination,
        "movement": movement,
        "x": f"{x:.3f}",
        "y": f"{y:.3f}",
        "speed": f"{speed:.3f}",
        "acceleration": f"{accel:.3f}",
    }


class RouteZoneEventsTest(unittest.TestCase):
    def test_extracts_only_matching_route_zone_events(self) -> None:
        artifact = build_route_geometry(cfg())
        zone = next(
            item for item in artifact["zones"]
            if set(item["route_ids"]) == {"r_N_left", "r_E_left"}
        )
        cx = float(zone["centroid"]["x"])
        cy = float(zone["centroid"]["y"])

        rows = [
            row(0.0, "h1", "r_N_left", cx, cy + 8.0),
            row(1.0, "h1", "r_N_left", cx, cy),
            row(2.0, "h1", "r_N_left", cx, cy),
            row(3.0, "h1", "r_N_left", cx, cy + 8.0),
            row(1.0, "c1", "r_S_through", cx, cy),
        ]

        events = extract_route_zone_events_from_rows(rows, artifact, pre_zone_window_s=3.0)

        self.assertEqual([event["veh_id"] for event in events], ["h1"])
        self.assertEqual(events[0]["zone_id"], zone["zone_id"])
        self.assertEqual(events[0]["zone_route_ids"], "r_N_left|r_E_left")
        self.assertEqual(events[0]["conflict_type"], zone["conflict_type"])
        self.assertEqual(events[0]["entry_time"], "1.0")
        self.assertEqual(events[0]["exit_time"], "2.0")

    def test_normalizes_sumo_coordinates_by_junction_center(self) -> None:
        artifact = build_route_geometry(cfg())
        zone = next(
            item for item in artifact["zones"]
            if set(item["route_ids"]) == {"r_N_left", "r_E_left"}
        )
        cx = float(zone["centroid"]["x"])
        cy = float(zone["centroid"]["y"])

        events = extract_route_zone_events_from_rows(
            [row(1.0, "h1", "r_N_left", cx, cy + 120.0)],
            artifact,
            pre_zone_window_s=3.0,
            coordinate_origin=(0.0, 120.0),
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["zone_id"], zone["zone_id"])


if __name__ == "__main__":
    unittest.main()
