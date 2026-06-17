from __future__ import annotations

import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_graph_prediction_dataset import _candidate_neighbors  # noqa: E402
from route_geometry import build_route_geometry  # noqa: E402


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


def indexed(row: dict) -> dict:
    return {"times": [float(row["time"])], "rows": [row]}


def state(veh_id: str, route_id: str) -> dict:
    origin = route_id.split("_")[1]
    movement = route_id.split("_")[2]
    return {
        "time": "1.0",
        "veh_id": veh_id,
        "veh_class": "HDV" if veh_id == "h" else "CAV",
        "route_id": route_id,
        "origin": origin,
        "movement": movement,
        "x": "0.0",
        "y": "0.0",
        "speed": "5.0",
        "acceleration": "0.0",
        "heading": "0.0",
        "distance_to_center": "999.0",
    }


class RouteZoneGraphDatasetTest(unittest.TestCase):
    def test_candidate_neighbors_use_route_zone_conflicts_when_artifact_is_available(self) -> None:
        artifact = build_route_geometry(cfg())
        states = {
            "h": indexed(state("h", "r_N_left")),
            "conflicting": indexed(state("conflicting", "r_E_left")),
            "compatible": indexed(state("compatible", "r_S_through")),
        }

        neighbors = _candidate_neighbors(
            states=states,
            target_id="h",
            sample_time=1.0,
            tolerance_s=0.1,
            conflict_radius_m=1.0,
            geometry_artifact=artifact,
        )

        self.assertEqual([item[0] for item in neighbors], ["conflicting"])
        self.assertEqual(neighbors[0][2]["shared_route_zone_id"], "r_N_left__r_E_left")
        self.assertEqual(neighbors[0][2]["route_conflict_type"], "overlap_turning")


if __name__ == "__main__":
    unittest.main()
