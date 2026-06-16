from __future__ import annotations

import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from safety_metrics import compute_conflict_safety_metrics, extract_zone_occupancies  # noqa: E402


def row(time: float, veh_id: str, origin: str, movement: str, distance: float) -> dict:
    return {
        "time": f"{time:.1f}",
        "veh_id": veh_id,
        "veh_class": "CAV",
        "origin": origin,
        "movement": movement,
        "distance_to_center": f"{distance:.1f}",
    }


class SafetyMetricsTest(unittest.TestCase):
    def test_extracts_zone_entry_and_exit(self) -> None:
        rows = [
            row(0.0, "a", "N", "through", 20.0),
            row(1.0, "a", "N", "through", 10.0),
            row(2.0, "a", "N", "through", 8.0),
            row(3.0, "a", "N", "through", 16.0),
        ]

        occupancies = extract_zone_occupancies(rows, zone_radius_m=14.0)

        self.assertEqual(len(occupancies), 1)
        self.assertEqual(occupancies[0].veh_id, "a")
        self.assertEqual(occupancies[0].entry_time, 1.0)
        self.assertEqual(occupancies[0].exit_time, 3.0)

    def test_computes_pet_between_conflicting_occupancies(self) -> None:
        rows = [
            row(0.0, "a", "N", "through", 20.0),
            row(1.0, "a", "N", "through", 10.0),
            row(2.0, "a", "N", "through", 16.0),
            row(0.0, "b", "E", "through", 20.0),
            row(4.0, "b", "E", "through", 10.0),
            row(5.0, "b", "E", "through", 16.0),
        ]

        metrics = compute_conflict_safety_metrics(rows, zone_radius_m=14.0, near_conflict_pet_s=1.5)

        self.assertEqual(metrics["conflict_pair_count"], 1)
        self.assertEqual(metrics["min_pet_s"], 2.0)
        self.assertEqual(metrics["near_conflict_count"], 0)
        self.assertEqual(metrics["min_entry_gap_s"], 3.0)

    def test_counts_near_conflict_when_pet_is_small_or_overlapping(self) -> None:
        rows = [
            row(0.0, "a", "N", "through", 20.0),
            row(1.0, "a", "N", "through", 10.0),
            row(3.0, "a", "N", "through", 16.0),
            row(0.0, "b", "E", "through", 20.0),
            row(2.0, "b", "E", "through", 10.0),
            row(4.0, "b", "E", "through", 16.0),
        ]

        metrics = compute_conflict_safety_metrics(rows, zone_radius_m=14.0, near_conflict_pet_s=1.5)

        self.assertEqual(metrics["conflict_pair_count"], 1)
        self.assertEqual(metrics["min_pet_s"], -1.0)
        self.assertEqual(metrics["near_conflict_count"], 1)

    def test_same_origin_pairs_are_not_counted_as_conflicts(self) -> None:
        rows = [
            row(1.0, "a", "N", "through", 10.0),
            row(2.0, "a", "N", "through", 16.0),
            row(2.2, "b", "N", "right", 10.0),
            row(3.0, "b", "N", "right", 16.0),
        ]

        metrics = compute_conflict_safety_metrics(rows, zone_radius_m=14.0, near_conflict_pet_s=1.5)

        self.assertEqual(metrics["conflict_pair_count"], 0)
        self.assertIsNone(metrics["min_pet_s"])
        self.assertEqual(metrics["near_conflict_count"], 0)

    def test_empty_rows_return_zero_counts(self) -> None:
        metrics = compute_conflict_safety_metrics([], zone_radius_m=14.0, near_conflict_pet_s=1.5)

        self.assertEqual(metrics["occupancy_count"], 0)
        self.assertEqual(metrics["conflict_pair_count"], 0)
        self.assertIsNone(metrics["min_pet_s"])


if __name__ == "__main__":
    unittest.main()
