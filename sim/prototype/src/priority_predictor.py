from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Protocol

from allocation_policy import VehicleState, estimate_arrival_time


class PriorityPredictor(Protocol):
    def predict(self, vehicle: VehicleState, candidates: list[VehicleState]) -> float:
        ...


class HeuristicPriorityPredictor:
    def predict(self, vehicle: VehicleState, candidates: list[VehicleState]) -> float:
        if vehicle.veh_class.upper() != "HDV":
            return 0.0
        cav_etas = [estimate_arrival_time(item) for item in candidates if item.veh_class.upper() == "CAV"]
        if not cav_etas:
            return 0.5
        eta_gap = min(cav_etas) - estimate_arrival_time(vehicle)
        return _sigmoid(eta_gap)


class LogisticPriorityPredictor:
    def __init__(
        self,
        feature_names: list[str],
        weights: list[float],
        bias: float,
        mean: list[float],
        std: list[float],
    ) -> None:
        self.feature_names = feature_names
        self.weights = weights
        self.bias = bias
        self.mean = mean
        self.std = [value if abs(value) > 1e-8 else 1.0 for value in std]

    @classmethod
    def from_summary(cls, path: str | Path) -> "LogisticPriorityPredictor":
        with Path(path).open("r", encoding="utf-8") as f:
            summary = json.load(f)
        return cls(
            feature_names=list(summary["feature_names"]),
            weights=[float(value) for value in summary["logistic_weights"]],
            bias=float(summary["logistic_bias"]),
            mean=[float(value) for value in summary["standardization_mean"]],
            std=[float(value) for value in summary["standardization_std"]],
        )

    def predict(self, vehicle: VehicleState, candidates: list[VehicleState]) -> float:
        if vehicle.veh_class.upper() != "HDV":
            return 0.0
        other = _select_reference_vehicle(vehicle, candidates)
        if other is None:
            return 0.5
        feature_map = _feature_map(vehicle, other)
        raw = [float(feature_map.get(name, 0.0)) for name in self.feature_names]
        standardized = [(value - mean) / std for value, mean, std in zip(raw, self.mean, self.std)]
        logit = sum(value * weight for value, weight in zip(standardized, self.weights)) + self.bias
        return _sigmoid(logit)


def load_priority_predictor(model_path: str | Path | None) -> PriorityPredictor:
    if not model_path:
        return HeuristicPriorityPredictor()
    path = Path(model_path)
    if not path.exists():
        return HeuristicPriorityPredictor()
    return LogisticPriorityPredictor.from_summary(path)


def _sigmoid(value: float) -> float:
    value = max(-40.0, min(40.0, float(value)))
    return 1.0 / (1.0 + math.exp(-value))


def _select_reference_vehicle(vehicle: VehicleState, candidates: list[VehicleState]) -> VehicleState | None:
    others = [item for item in candidates if item.veh_id != vehicle.veh_id]
    if not others:
        return None
    return min(others, key=lambda item: (abs(estimate_arrival_time(item) - estimate_arrival_time(vehicle)), item.veh_id))


def _feature_map(hdv: VehicleState, other: VehicleState) -> dict[str, float]:
    hdv_eta = estimate_arrival_time(hdv)
    other_eta = estimate_arrival_time(other)
    return {
        "relative_distance": abs(hdv.distance_to_center - other.distance_to_center),
        "relative_speed_hdv_minus_other": hdv.speed - other.speed,
        "distance_to_center_hdv_minus_other": hdv.distance_to_center - other.distance_to_center,
        "estimated_ttcp_hdv": hdv_eta,
        "estimated_ttcp_other": other_eta,
        "estimated_ttcp_diff_hdv_minus_other": hdv_eta - other_eta,
        "same_movement": 0.0,
        "other_is_cav": 1.0 if other.veh_class.upper() == "CAV" else 0.0,
        "hdv_x": 0.0,
        "hdv_y": 0.0,
        "hdv_speed": hdv.speed,
        "hdv_acceleration": 0.0,
        "hdv_heading": 0.0,
        "hdv_distance_to_center": hdv.distance_to_center,
        "other_x": 0.0,
        "other_y": 0.0,
        "other_speed": other.speed,
        "other_acceleration": 0.0,
        "other_heading": 0.0,
        "other_distance_to_center": other.distance_to_center,
    }
