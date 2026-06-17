from __future__ import annotations

import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from common import PROTOTYPE_ROOT, scenario_run_id  # noqa: E402
from generate_network import generate_network  # noqa: E402
from generate_routes import build_routes  # noqa: E402
from render_network_preview import render_preview  # noqa: E402
from train_prediction_baselines import seed_from_run_id  # noqa: E402


def _write_t_config(path: Path) -> None:
    payload = {
        "scenario_name": "t_junction_unsignalized_test",
        "intersection_type": "t_junction",
        "active_approaches": ["N", "E", "S"],
        "step_length": 0.1,
        "speed_limit_mps": 11.11,
        "approach_length_m": 120.0,
        "incoming_lane_count": 1,
        "outgoing_lane_count": 1,
        "traffic_volumes_veh_per_hour_per_approach": {
            "low": 300,
            "medium": 600,
            "high": 900,
        },
        "turning_ratio": {
            "left": 0.25,
            "through": 0.5,
            "right": 0.25,
        },
        "hdv_behavior_profiles": {
            "normal": {
                "tau": 1.1,
                "accel": 2.6,
                "decel": 4.0,
                "minGap": 2.5,
                "sigma": 0.5,
            },
        },
        "hdv_behavior_mix": {"normal": 1.0},
        "conflict_zones": [
            {
                "zone_id": "center",
                "center_x": 0.0,
                "center_y": 0.0,
                "radius_m": 12.0,
            }
        ],
        "label_thresholds": {},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class TJunctionGeometryTest(unittest.TestCase):
    def test_scenario_run_id_keeps_four_leg_compatibility_and_prefixes_t_junction(self) -> None:
        four_leg_cfg = {"scenario_name": "four_leg_unsignalized_p0"}
        t_cfg = {
            "scenario_name": "t_junction_unsignalized_test",
            "intersection_type": "t_junction",
            "active_approaches": ["N", "E", "S"],
        }

        self.assertEqual(scenario_run_id(four_leg_cfg, 1, "low", 0.5), "seed1_low_pen50")
        self.assertEqual(
            scenario_run_id({"intersection_type": "four_leg", "active_approaches": ["S", "N", "W", "E"]}, 1, "low", 0.5),
            "seed1_low_pen50",
        )
        self.assertEqual(
            scenario_run_id(t_cfg, 1, "low", 0.5),
            "t_junction_unsignalized_test_seed1_low_pen50",
        )
        self.assertEqual(seed_from_run_id("t_junction_unsignalized_test_seed7_medium_pen50"), 7)

    def test_t_junction_network_uses_only_active_approaches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "t_config.json"
            _write_t_config(config_path)

            with patch("generate_network.subprocess.run"):
                outputs = generate_network(str(config_path))

            nodes = ET.parse(outputs["nodes"]).getroot()
            edges = ET.parse(outputs["edges"]).getroot()
            connections = ET.parse(outputs["connections"]).getroot()

            node_ids = {node.attrib["id"] for node in nodes}
            edge_ids = {edge.attrib["id"] for edge in edges}
            connection_pairs = {
                (conn.attrib["from"], conn.attrib["to"])
                for conn in connections
            }

            self.assertEqual(node_ids, {"C", "N0", "E0", "S0"})
            self.assertEqual(
                edge_ids,
                {"N_in", "N_out", "E_in", "E_out", "S_in", "S_out"},
            )
            self.assertEqual(
                connection_pairs,
                {
                    ("N_in", "E_out"),
                    ("N_in", "S_out"),
                    ("E_in", "N_out"),
                    ("E_in", "S_out"),
                    ("S_in", "N_out"),
                    ("S_in", "E_out"),
                },
            )

    def test_t_junction_routes_exclude_unavailable_movements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "t_config.json"
            _write_t_config(config_path)

            outputs = build_routes(
                str(config_path),
                seed=1,
                volume="low",
                penetration=0.5,
                duration=60.0,
            )

            self.assertEqual(
                outputs["routes"].parent.name,
                "t_junction_unsignalized_test_seed1_low_pen50",
            )
            routes = ET.parse(outputs["routes"]).getroot()
            route_edges = {
                route.attrib["id"]: route.attrib["edges"]
                for route in routes.findall("route")
            }
            route_meta = json.loads(outputs["metadata"].read_text(encoding="utf-8"))

            self.assertEqual(
                set(route_edges),
                {
                    "r_N_left",
                    "r_N_through",
                    "r_E_left",
                    "r_E_right",
                    "r_S_through",
                    "r_S_right",
                },
            )
            self.assertEqual(route_edges["r_N_left"], "N_in E_out")
            self.assertEqual(route_edges["r_N_through"], "N_in S_out")
            self.assertEqual(route_edges["r_E_left"], "E_in S_out")
            self.assertEqual(route_edges["r_E_right"], "E_in N_out")
            self.assertEqual(route_edges["r_S_through"], "S_in N_out")
            self.assertEqual(route_edges["r_S_right"], "S_in E_out")
            self.assertNotIn("r_W_left", route_meta["route_meta"])
            self.assertNotIn("r_N_right", route_meta["route_meta"])

    def test_preview_normalizes_sumo_net_offset_to_center_junction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = tmp_path / "t_config.json"
            net_path = tmp_path / "offset.net.xml"
            output_path = tmp_path / "preview.svg"
            _write_t_config(config_path)
            net_path.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<net>
  <junction id="C" x="0.00" y="120.00" type="priority" />
  <junction id="N0" x="0.00" y="240.00" type="dead_end" />
  <junction id="E0" x="120.00" y="120.00" type="dead_end" />
  <junction id="S0" x="0.00" y="0.00" type="dead_end" />
</net>
""",
                encoding="utf-8",
            )

            render_preview(config_path, net_path, output_path)

            svg = output_path.read_text(encoding="utf-8")
            self.assertIn('x1="450.0" y1="155.0" x2="450.0" y2="745.0"', svg)
            self.assertIn('x1="745.0" y1="450.0" x2="450.0" y2="450.0"', svg)
            self.assertNotIn('y1="-270.0"', svg)


if __name__ == "__main__":
    unittest.main()
