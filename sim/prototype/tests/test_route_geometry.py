from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from route_geometry import build_route_geometry, write_route_geometry  # noqa: E402


def _cfg() -> dict:
    return {
        "scenario_name": "t_junction_unsignalized_test",
        "intersection_type": "t_junction",
        "active_approaches": ["N", "E", "S"],
        "approach_length_m": 120.0,
        "lane_width_m": 3.5,
        "turn_radius_m": 10.0,
        "vehicle_dimensions_m": {"length": 4.8, "width": 1.9},
        "geometry_safety_buffer_m": 0.5,
        "control_region_distance_m": 30.0,
        "path_sample_interval_m": 2.0,
        "static_overlap_tolerance_m2": 0.1,
        "geometry_mode": "lane_offset_paths",
    }


class RouteGeometryTest(unittest.TestCase):
    def test_builds_only_legal_t_junction_routes_with_sampled_paths(self) -> None:
        geometry = build_route_geometry(_cfg())

        self.assertEqual(
            set(geometry["routes"]),
            {
                "r_N_left",
                "r_N_through",
                "r_S_through",
                "r_S_right",
                "r_E_right",
                "r_E_left",
            },
        )
        self.assertNotIn("r_N_right", geometry["routes"])
        self.assertNotIn("r_W_left", geometry["routes"])

        path = geometry["routes"]["r_N_through"]["path"]
        self.assertGreater(len(path), 10)
        self.assertEqual(path[0]["s_m"], 0.0)
        self.assertEqual(path[0]["x"], 1.75)
        self.assertEqual(path[-1]["x"], -1.75)
        self.assertGreater(path[-1]["s_m"], path[0]["s_m"])
        self.assertTrue(all(path[index]["s_m"] <= path[index + 1]["s_m"] for index in range(len(path) - 1)))

    def test_lane_offsets_place_opposing_through_lanes_on_different_sides(self) -> None:
        geometry = build_route_geometry(_cfg())

        n_start = geometry["routes"]["r_N_through"]["path"][0]
        s_start = geometry["routes"]["r_S_through"]["path"][0]

        self.assertAlmostEqual(n_start["x"], 1.75)
        self.assertAlmostEqual(s_start["x"], -1.75)
        self.assertGreater(n_start["y"], 0.0)
        self.assertLess(s_start["y"], 0.0)

    def test_conflict_matrix_is_symmetric_and_has_expected_route_pairs(self) -> None:
        geometry = build_route_geometry(_cfg())
        matrix = geometry["conflict_matrix"]

        self.assertFalse(matrix["r_N_through"]["r_S_through"])
        self.assertFalse(matrix["r_S_through"]["r_N_through"])
        self.assertTrue(matrix["r_N_left"]["r_E_left"])
        self.assertTrue(matrix["r_E_left"]["r_N_left"])
        self.assertIn("r_N_left__r_E_left", geometry["conflict_zones"])
        self.assertNotIn("r_N_through__r_S_through", geometry["conflict_zones"])

    def test_write_route_geometry_serializes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "geometry.json"

            written = write_route_geometry(_cfg(), path)

            self.assertEqual(written, path)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["scenario_name"], "t_junction_unsignalized_test")
            self.assertIn("r_E_right", loaded["routes"])


if __name__ == "__main__":
    unittest.main()
