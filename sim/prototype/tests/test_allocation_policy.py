from __future__ import annotations

import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from allocation_policy import VehicleState, build_decision, estimate_arrival_time, fairness_gini  # noqa: E402


class AllocationPolicyTest(unittest.TestCase):
    def test_fcfs_orders_by_estimated_arrival_time(self) -> None:
        vehicles = [
            VehicleState("late", "CAV", distance_to_center=30.0, speed=5.0, waiting_time=0.0),
            VehicleState("early", "CAV", distance_to_center=15.0, speed=5.0, waiting_time=0.0),
        ]

        decision = build_decision(vehicles, method="fcfs")

        self.assertEqual(decision.release_order, ["early", "late"])
        self.assertEqual(decision.hold_vehicles, ["late"])

    def test_prediction_guided_policy_yields_to_high_risk_hdv(self) -> None:
        vehicles = [
            VehicleState("cav", "CAV", distance_to_center=18.0, speed=6.0, waiting_time=0.0),
            VehicleState("hdv", "HDV", distance_to_center=28.0, speed=7.0, waiting_time=0.0, priority_probability=0.9),
        ]

        decision = build_decision(vehicles, method="prediction_coalition", risk_threshold=0.7)

        self.assertEqual(decision.release_order[0], "hdv")
        self.assertIn("cav", decision.hold_vehicles)

    def test_fairness_weight_can_promote_long_waiting_vehicle(self) -> None:
        vehicles = [
            VehicleState("fast", "CAV", distance_to_center=15.0, speed=5.0, waiting_time=0.0),
            VehicleState("patient", "CAV", distance_to_center=25.0, speed=5.0, waiting_time=18.0),
        ]

        decision = build_decision(vehicles, method="prediction_coalition", fairness_weight=0.4)

        self.assertEqual(decision.release_order[0], "patient")

    def test_coalition_releases_multiple_low_conflict_cavs(self) -> None:
        vehicles = [
            VehicleState("cav_a", "CAV", distance_to_center=10.0, speed=5.0, waiting_time=0.0),
            VehicleState("cav_b", "CAV", distance_to_center=18.0, speed=5.0, waiting_time=0.0),
            VehicleState("cav_c", "CAV", distance_to_center=26.0, speed=5.0, waiting_time=0.0),
        ]

        decision = build_decision(
            vehicles,
            method="prediction_coalition",
            max_release_count=3,
            safe_arrival_gap_s=1.0,
        )

        self.assertEqual(decision.release_vehicles, ["cav_a", "cav_b", "cav_c"])
        self.assertEqual(decision.hold_vehicles, [])

    def test_coalition_blocks_near_simultaneous_cav(self) -> None:
        vehicles = [
            VehicleState("cav_a", "CAV", distance_to_center=10.0, speed=5.0, waiting_time=0.0),
            VehicleState("cav_b", "CAV", distance_to_center=11.0, speed=5.0, waiting_time=0.0),
        ]

        decision = build_decision(
            vehicles,
            method="prediction_coalition",
            max_release_count=2,
            safe_arrival_gap_s=1.0,
        )

        self.assertEqual(decision.release_vehicles, ["cav_a"])
        self.assertEqual(decision.hold_vehicles, ["cav_b"])

    def test_coalition_holds_cav_when_high_risk_hdv_has_close_arrival(self) -> None:
        vehicles = [
            VehicleState("cav", "CAV", distance_to_center=10.0, speed=5.0, waiting_time=0.0),
            VehicleState("hdv", "HDV", distance_to_center=11.0, speed=5.0, waiting_time=0.0, priority_probability=0.9),
        ]

        decision = build_decision(
            vehicles,
            method="prediction_coalition",
            risk_threshold=0.7,
            max_release_count=2,
            safe_arrival_gap_s=1.0,
        )

        self.assertEqual(decision.release_vehicles, ["hdv"])
        self.assertIn("cav", decision.hold_vehicles)

    def test_arrival_time_is_finite_for_stopped_vehicle(self) -> None:
        vehicle = VehicleState("stopped", "CAV", distance_to_center=12.0, speed=0.0, waiting_time=0.0)

        self.assertEqual(estimate_arrival_time(vehicle), 12.0)

    def test_fairness_gini_is_zero_for_equal_waits(self) -> None:
        self.assertEqual(fairness_gini([3.0, 3.0, 3.0]), 0.0)
        self.assertGreater(fairness_gini([0.0, 0.0, 9.0]), 0.0)


if __name__ == "__main__":
    unittest.main()
