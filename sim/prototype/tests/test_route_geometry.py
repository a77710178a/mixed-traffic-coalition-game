from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from route_geometry import build_route_geometry, write_route_geometry  # noqa: E402


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "t_junction_scenario.json"


def _cfg() -> dict:
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


class RouteGeometryTest(unittest.TestCase):
    def test_t_junction_config_uses_approved_nominal_geometry_values(self) -> None:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

        self.assertEqual(cfg["vehicle_dimensions_m"], {"length": 4.5, "width": 1.8})
        self.assertEqual(cfg["control_region_distance_m"], 45.0)
        self.assertEqual(cfg["path_sample_interval_m"], 0.25)
        self.assertEqual(cfg["static_overlap_tolerance_m2"], 0.25)
        self.assertEqual(cfg["geometry_mode"], "route_zones")

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
        self.assertEqual(path[0]["x"], -1.75)
        self.assertEqual(path[-1]["x"], -1.75)
        self.assertGreater(path[-1]["s_m"], path[0]["s_m"])
        self.assertTrue(all(path[index]["s_m"] <= path[index + 1]["s_m"] for index in range(len(path) - 1)))

    def test_lane_offsets_match_written_inbound_convention(self) -> None:
        geometry = build_route_geometry(_cfg())

        n_start = geometry["routes"]["r_N_through"]["path"][0]
        s_start = geometry["routes"]["r_S_through"]["path"][0]
        e_start = geometry["routes"]["r_E_left"]["path"][0]

        self.assertAlmostEqual(n_start["x"], -1.75)
        self.assertAlmostEqual(s_start["x"], 1.75)
        self.assertAlmostEqual(e_start["y"], 1.75)
        self.assertGreater(n_start["y"], 0.0)
        self.assertLess(s_start["y"], 0.0)
        self.assertGreater(e_start["x"], 0.0)

    def test_conflict_matrix_uses_relation_objects_and_primary_zones(self) -> None:
        geometry = build_route_geometry(_cfg())
        matrix = geometry["conflict_matrix"]
        zones = {zone["zone_id"]: zone for zone in geometry["zones"]}

        self.assertEqual(matrix["r_N_through"]["r_S_through"]["conflict_type"], "none")
        self.assertFalse(matrix["r_N_through"]["r_S_through"]["conflicts"])
        self.assertEqual(matrix["r_S_through"]["r_N_through"], matrix["r_N_through"]["r_S_through"])

        relation = matrix["r_N_left"]["r_E_left"]
        self.assertTrue(relation["conflicts"])
        self.assertEqual(relation["conflict_type"], "overlap_turning")
        self.assertEqual(matrix["r_E_left"]["r_N_left"], relation)
        self.assertIn("r_N_left__r_E_left", relation["zone_ids"])
        self.assertIn("r_N_left__r_E_left", zones)
        zone = zones["r_N_left__r_E_left"]
        self.assertEqual(zone["route_ids"], ["r_N_left", "r_E_left"])
        self.assertEqual(zone["conflict_type"], "overlap_turning")
        self.assertIn("r_N_left", zone["entry_distance_by_route"])
        self.assertIn("r_E_left", zone["exit_distance_by_route"])
        self.assertNotIn("r_N_through__r_S_through", geometry["conflict_zones"])

    def test_same_origin_route_pairs_are_diverging_constraints_with_zones(self) -> None:
        geometry = build_route_geometry(_cfg())
        relation = geometry["conflict_matrix"]["r_N_through"]["r_N_left"]

        self.assertTrue(relation["conflicts"])
        self.assertEqual(relation["conflict_type"], "diverging")
        self.assertEqual(relation["zone_ids"], ["r_N_through__r_N_left"])
        zones = {zone["zone_id"]: zone for zone in geometry["zones"]}
        self.assertEqual(zones["r_N_through__r_N_left"]["route_ids"], ["r_N_through", "r_N_left"])

    def test_every_nonzero_non_diagonal_matrix_entry_maps_to_a_zone(self) -> None:
        geometry = build_route_geometry(_cfg())
        zone_ids = {zone["zone_id"] for zone in geometry["zones"]}

        for route_id, row in geometry["conflict_matrix"].items():
            for other_id, relation in row.items():
                if route_id == other_id or not relation["conflicts"]:
                    continue
                self.assertGreater(len(relation["zone_ids"]), 0)
                self.assertTrue(set(relation["zone_ids"]).issubset(zone_ids))

    def test_conflict_relations_are_stable_across_sample_intervals(self) -> None:
        fine = build_route_geometry({**_cfg(), "path_sample_interval_m": 0.25})
        coarse = build_route_geometry({**_cfg(), "path_sample_interval_m": 2.0})

        for route_id, row in fine["conflict_matrix"].items():
            for other_id, relation in row.items():
                self.assertEqual(coarse["conflict_matrix"][route_id][other_id]["conflicts"], relation["conflicts"])
                self.assertEqual(coarse["conflict_matrix"][route_id][other_id]["conflict_type"], relation["conflict_type"])

    def test_artifact_parameters_document_distance_threshold_approximation(self) -> None:
        geometry = build_route_geometry(_cfg())

        self.assertEqual(geometry["parameters"]["static_overlap_tolerance_m2"], 0.25)
        self.assertEqual(geometry["parameters"]["overlap_method"], "segment_distance_threshold")
        self.assertEqual(geometry["parameters"]["distance_threshold_m"], 2.8)

    def test_write_route_geometry_serializes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "geometry.json"

            written = write_route_geometry(_cfg(), path)

            self.assertEqual(written, path)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["scenario_name"], "t_junction_unsignalized_test")
            self.assertIn("r_E_right", loaded["routes"])
            self.assertIn("zones", loaded)


if __name__ == "__main__":
    unittest.main()
