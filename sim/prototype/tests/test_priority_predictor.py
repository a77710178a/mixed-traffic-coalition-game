from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from allocation_policy import VehicleState  # noqa: E402
from priority_predictor import HeuristicPriorityPredictor, LogisticPriorityPredictor, load_priority_predictor  # noqa: E402


class PriorityPredictorTest(unittest.TestCase):
    def test_heuristic_predictor_returns_probability_for_hdv(self) -> None:
        predictor = HeuristicPriorityPredictor()
        hdv = VehicleState("hdv", "HDV", distance_to_center=10.0, speed=5.0, waiting_time=0.0)
        cav = VehicleState("cav", "CAV", distance_to_center=20.0, speed=5.0, waiting_time=0.0)

        prob = predictor.predict(hdv, [hdv, cav])

        self.assertGreater(prob, 0.5)
        self.assertEqual(predictor.predict(cav, [hdv, cav]), 0.0)

    def test_logistic_predictor_loads_summary_and_scores_hdv(self) -> None:
        feature_names = [
            "relative_distance",
            "relative_speed_hdv_minus_other",
            "distance_to_center_hdv_minus_other",
            "estimated_ttcp_hdv",
            "estimated_ttcp_other",
            "estimated_ttcp_diff_hdv_minus_other",
            "same_movement",
            "other_is_cav",
            "hdv_x",
            "hdv_y",
            "hdv_speed",
            "hdv_acceleration",
            "hdv_heading",
            "hdv_distance_to_center",
            "other_x",
            "other_y",
            "other_speed",
            "other_acceleration",
            "other_heading",
            "other_distance_to_center",
        ]
        summary = {
            "feature_names": feature_names,
            "logistic_weights": [0.0] * len(feature_names),
            "logistic_bias": 0.0,
            "standardization_mean": [0.0] * len(feature_names),
            "standardization_std": [1.0] * len(feature_names),
        }

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(summary), encoding="utf-8")
            predictor = LogisticPriorityPredictor.from_summary(path)

        hdv = VehicleState("hdv", "HDV", distance_to_center=10.0, speed=5.0, waiting_time=0.0)
        cav = VehicleState("cav", "CAV", distance_to_center=20.0, speed=5.0, waiting_time=0.0)

        self.assertEqual(predictor.predict(hdv, [hdv, cav]), 0.5)

    def test_loader_falls_back_to_heuristic_without_model_path(self) -> None:
        predictor = load_priority_predictor(None)

        self.assertIsInstance(predictor, HeuristicPriorityPredictor)


if __name__ == "__main__":
    unittest.main()
