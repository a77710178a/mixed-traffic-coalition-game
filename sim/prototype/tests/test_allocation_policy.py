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

    def test_cav_waiting_tiebreaker_can_promote_long_waiting_cav(self) -> None:
        vehicles = [
            VehicleState("fast", "CAV", distance_to_center=15.0, speed=5.0, waiting_time=0.0),
            VehicleState("patient", "CAV", distance_to_center=25.0, speed=5.0, waiting_time=18.0),
        ]

        decision = build_decision(
            vehicles,
            method="prediction_coalition",
            fairness_weight=0.0,
            cav_waiting_tiebreaker_weight=0.2,
        )

        self.assertEqual(decision.release_order[0], "patient")

    def test_cav_waiting_tiebreaker_does_not_bypass_high_risk_hdv_gap(self) -> None:
        vehicles = [
            VehicleState("cav", "CAV", distance_to_center=10.0, speed=5.0, waiting_time=30.0),
            VehicleState("hdv", "HDV", distance_to_center=11.0, speed=5.0, waiting_time=0.0, priority_probability=0.9),
        ]

        decision = build_decision(
            vehicles,
            method="prediction_coalition",
            risk_threshold=0.7,
            max_release_count=2,
            safe_arrival_gap_s=1.0,
            cav_waiting_tiebreaker_weight=0.2,
        )

        self.assertEqual(decision.release_vehicles, ["hdv"])
        self.assertIn("cav", decision.hold_vehicles)

    def test_adaptive_gate_adds_low_risk_cav_on_non_conflicting_route(self) -> None:
        vehicles = [
            VehicleState("a", "CAV", distance_to_center=10.0, speed=5.0, waiting_time=0.0, route_id="r_N_through"),
            VehicleState("b", "CAV", distance_to_center=18.0, speed=5.0, waiting_time=0.0, route_id="r_S_through"),
            VehicleState("c", "CAV", distance_to_center=26.0, speed=5.0, waiting_time=0.0, route_id="r_E_right"),
        ]
        route_conflicts = {
            "r_N_through": {"r_S_through": {"conflicts": False}, "r_E_right": {"conflicts": False}},
            "r_S_through": {"r_N_through": {"conflicts": False}, "r_E_right": {"conflicts": False}},
            "r_E_right": {"r_N_through": {"conflicts": False}, "r_S_through": {"conflicts": False}},
        }

        decision = build_decision(
            vehicles,
            method="prediction_coalition",
            max_release_count=2,
            safe_arrival_gap_s=1.0,
            adaptive_release_enabled=True,
            adaptive_max_release_count=3,
            route_conflict_matrix=route_conflicts,
            conflict_zone_occupancy=0,
        )

        self.assertEqual(decision.release_vehicles, ["a", "b", "c"])
        self.assertEqual(decision.hold_vehicles, [])

    def test_adaptive_gate_blocks_conflicting_cav_without_extra_gap(self) -> None:
        vehicles = [
            VehicleState("a", "CAV", distance_to_center=10.0, speed=5.0, waiting_time=0.0, route_id="r_N_left"),
            VehicleState("b", "CAV", distance_to_center=18.0, speed=5.0, waiting_time=0.0, route_id="r_S_right"),
            VehicleState("c", "CAV", distance_to_center=26.0, speed=5.0, waiting_time=0.0, route_id="r_E_left"),
        ]
        route_conflicts = {
            "r_N_left": {"r_S_right": {"conflicts": False}, "r_E_left": {"conflicts": True}},
            "r_S_right": {"r_N_left": {"conflicts": False}, "r_E_left": {"conflicts": False}},
            "r_E_left": {"r_N_left": {"conflicts": True}, "r_S_right": {"conflicts": False}},
        }

        decision = build_decision(
            vehicles,
            method="prediction_coalition",
            max_release_count=2,
            safe_arrival_gap_s=1.0,
            adaptive_release_enabled=True,
            adaptive_max_release_count=3,
            adaptive_min_conflict_arrival_gap_s=6.0,
            route_conflict_matrix=route_conflicts,
            conflict_zone_occupancy=0,
        )

        self.assertEqual(decision.release_vehicles, ["a", "b"])
        self.assertIn("c", decision.hold_vehicles)

    def test_adaptive_gate_blocks_extra_release_when_zone_is_occupied(self) -> None:
        vehicles = [
            VehicleState("a", "CAV", distance_to_center=10.0, speed=5.0, waiting_time=0.0, route_id="r_N_through"),
            VehicleState("b", "CAV", distance_to_center=18.0, speed=5.0, waiting_time=0.0, route_id="r_S_through"),
            VehicleState("c", "CAV", distance_to_center=26.0, speed=5.0, waiting_time=0.0, route_id="r_E_right"),
        ]
        route_conflicts = {
            "r_N_through": {"r_S_through": {"conflicts": False}, "r_E_right": {"conflicts": False}},
            "r_S_through": {"r_N_through": {"conflicts": False}, "r_E_right": {"conflicts": False}},
            "r_E_right": {"r_N_through": {"conflicts": False}, "r_S_through": {"conflicts": False}},
        }

        decision = build_decision(
            vehicles,
            method="prediction_coalition",
            max_release_count=2,
            safe_arrival_gap_s=1.0,
            adaptive_release_enabled=True,
            adaptive_max_release_count=3,
            adaptive_max_occupancy=0,
            route_conflict_matrix=route_conflicts,
            conflict_zone_occupancy=1,
        )

        self.assertEqual(decision.release_vehicles, ["a", "b"])
        self.assertIn("c", decision.hold_vehicles)

    def test_adaptive_gate_does_not_bypass_high_risk_hdv_gap(self) -> None:
        vehicles = [
            VehicleState("hdv", "HDV", distance_to_center=10.0, speed=5.0, waiting_time=0.0, priority_probability=0.9, route_id="r_N_left"),
            VehicleState("cav_a", "CAV", distance_to_center=18.0, speed=5.0, waiting_time=0.0, route_id="r_S_through"),
            VehicleState("cav_b", "CAV", distance_to_center=11.0, speed=5.0, waiting_time=0.0, route_id="r_E_left"),
        ]
        route_conflicts = {
            "r_N_left": {"r_S_through": {"conflicts": False}, "r_E_left": {"conflicts": False}},
            "r_S_through": {"r_N_left": {"conflicts": False}, "r_E_left": {"conflicts": False}},
            "r_E_left": {"r_N_left": {"conflicts": False}, "r_S_through": {"conflicts": False}},
        }

        decision = build_decision(
            vehicles,
            method="prediction_coalition",
            risk_threshold=0.7,
            max_release_count=2,
            safe_arrival_gap_s=1.0,
            adaptive_release_enabled=True,
            adaptive_max_release_count=3,
            route_conflict_matrix=route_conflicts,
            conflict_zone_occupancy=0,
        )

        self.assertEqual(decision.release_vehicles, ["hdv", "cav_a"])
        self.assertIn("cav_b", decision.hold_vehicles)

    def test_adaptive_gate_is_disabled_by_default(self) -> None:
        vehicles = [
            VehicleState("a", "CAV", distance_to_center=10.0, speed=5.0, waiting_time=0.0, route_id="r_N_through"),
            VehicleState("b", "CAV", distance_to_center=18.0, speed=5.0, waiting_time=0.0, route_id="r_S_through"),
            VehicleState("c", "CAV", distance_to_center=26.0, speed=5.0, waiting_time=0.0, route_id="r_E_right"),
        ]

        decision = build_decision(
            vehicles,
            method="prediction_coalition",
            max_release_count=2,
            safe_arrival_gap_s=1.0,
        )

        self.assertEqual(decision.release_vehicles, ["a", "b"])
        self.assertIn("c", decision.hold_vehicles)

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
