from __future__ import annotations

import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from safety_metrics import compute_route_zone_safety_metrics  # noqa: E402


class RouteZoneSafetyMetricsTest(unittest.TestCase):
    def test_counts_only_conflicting_route_zone_pairs(self) -> None:
        events = [
            {
                "veh_id": "a",
                "veh_class": "CAV",
                "origin": "N",
                "destination": "S",
                "movement": "through",
                "route_id": "r_N_through",
                "zone_id": "z_major",
                "zone_route_ids": "r_N_through|r_S_through",
                "conflict_type": "none",
                "entry_time": "1.0",
                "exit_time": "2.0",
            },
            {
                "veh_id": "b",
                "veh_class": "CAV",
                "origin": "S",
                "destination": "N",
                "movement": "through",
                "route_id": "r_S_through",
                "zone_id": "z_major",
                "zone_route_ids": "r_N_through|r_S_through",
                "conflict_type": "none",
                "entry_time": "1.2",
                "exit_time": "2.2",
            },
        ]

        metrics = compute_route_zone_safety_metrics(events, near_conflict_pet_s=1.5)

        self.assertEqual(metrics["occupancy_count"], 2)
        self.assertEqual(metrics["conflict_pair_count"], 0)
        self.assertEqual(metrics["near_conflict_count"], 0)


if __name__ == "__main__":
    unittest.main()
