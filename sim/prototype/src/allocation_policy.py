from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VehicleState:
    veh_id: str
    veh_class: str
    distance_to_center: float
    speed: float
    waiting_time: float
    priority_probability: float = 0.5


@dataclass(frozen=True)
class AllocationDecision:
    release_order: list[str]
    hold_vehicles: list[str]
    scores: dict[str, float]


def estimate_arrival_time(vehicle: VehicleState, min_speed: float = 1.0) -> float:
    return max(0.0, float(vehicle.distance_to_center)) / max(min_speed, float(vehicle.speed))


def fairness_gini(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(max(0.0, float(value)) for value in values)
    total = sum(sorted_values)
    if total <= 0.0:
        return 0.0
    weighted_sum = sum((index + 1) * value for index, value in enumerate(sorted_values))
    n = len(sorted_values)
    return (2.0 * weighted_sum) / (n * total) - (n + 1.0) / n


def _fcfs_score(vehicle: VehicleState) -> float:
    return estimate_arrival_time(vehicle)


def _prediction_coalition_score(
    vehicle: VehicleState,
    risk_threshold: float,
    fairness_weight: float,
    hdv_priority_bonus: float,
) -> float:
    arrival = estimate_arrival_time(vehicle)
    fairness_credit = fairness_weight * max(0.0, float(vehicle.waiting_time))
    risk_credit = 0.0
    if vehicle.veh_class.upper() == "HDV" and float(vehicle.priority_probability) >= risk_threshold:
        risk_credit = hdv_priority_bonus * float(vehicle.priority_probability)
    return arrival - fairness_credit - risk_credit


def build_decision(
    vehicles: list[VehicleState],
    method: str,
    risk_threshold: float = 0.7,
    fairness_weight: float = 0.0,
    hdv_priority_bonus: float = 8.0,
    release_count: int = 1,
) -> AllocationDecision:
    if not vehicles:
        return AllocationDecision(release_order=[], hold_vehicles=[], scores={})

    if method == "fcfs":
        scores = {vehicle.veh_id: _fcfs_score(vehicle) for vehicle in vehicles}
    elif method in {"prediction_fcfs", "prediction_coalition"}:
        scores = {
            vehicle.veh_id: _prediction_coalition_score(
                vehicle,
                risk_threshold=risk_threshold,
                fairness_weight=fairness_weight if method == "prediction_coalition" else 0.0,
                hdv_priority_bonus=hdv_priority_bonus,
            )
            for vehicle in vehicles
        }
    else:
        raise ValueError(f"Unknown allocation method: {method}")

    release_order = [
        vehicle.veh_id
        for vehicle in sorted(
            vehicles,
            key=lambda item: (
                scores[item.veh_id],
                estimate_arrival_time(item),
                item.veh_id,
            ),
        )
    ]
    release_set = set(release_order[: max(1, int(release_count))])
    hold_vehicles = [veh_id for veh_id in release_order if veh_id not in release_set]
    return AllocationDecision(release_order=release_order, hold_vehicles=hold_vehicles, scores=scores)
