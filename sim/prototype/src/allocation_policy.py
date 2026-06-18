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
    release_vehicles: list[str] | None = None


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
    cav_waiting_tiebreaker_weight: float,
) -> float:
    arrival = estimate_arrival_time(vehicle)
    fairness_credit = fairness_weight * max(0.0, float(vehicle.waiting_time))
    cav_waiting_credit = 0.0
    if vehicle.veh_class.upper() == "CAV":
        cav_waiting_credit = cav_waiting_tiebreaker_weight * max(0.0, float(vehicle.waiting_time))
    risk_credit = 0.0
    if vehicle.veh_class.upper() == "HDV" and float(vehicle.priority_probability) >= risk_threshold:
        risk_credit = hdv_priority_bonus * float(vehicle.priority_probability)
    return arrival - fairness_credit - cav_waiting_credit - risk_credit


def _is_close_arrival(a: VehicleState, b: VehicleState, safe_arrival_gap_s: float) -> bool:
    return abs(estimate_arrival_time(a) - estimate_arrival_time(b)) < safe_arrival_gap_s


def _select_release_set(
    ordered: list[VehicleState],
    method: str,
    risk_threshold: float,
    max_release_count: int,
    safe_arrival_gap_s: float,
) -> list[str]:
    if not ordered:
        return []
    if method != "prediction_coalition":
        return [ordered[0].veh_id]

    release: list[VehicleState] = []
    high_risk_hdvs = [
        vehicle
        for vehicle in ordered
        if vehicle.veh_class.upper() == "HDV" and vehicle.priority_probability >= risk_threshold
    ]

    for vehicle in ordered:
        if len(release) >= max(1, int(max_release_count)):
            break
        if any(_is_close_arrival(vehicle, selected, safe_arrival_gap_s) for selected in release):
            continue
        if vehicle.veh_class.upper() == "CAV" and any(
            _is_close_arrival(vehicle, hdv, safe_arrival_gap_s) and hdv.veh_id not in {item.veh_id for item in release}
            for hdv in high_risk_hdvs
        ):
            continue
        release.append(vehicle)
    if not release:
        release.append(ordered[0])
    return [vehicle.veh_id for vehicle in release]


def build_decision(
    vehicles: list[VehicleState],
    method: str,
    risk_threshold: float = 0.7,
    fairness_weight: float = 0.0,
    hdv_priority_bonus: float = 8.0,
    release_count: int = 1,
    max_release_count: int | None = None,
    safe_arrival_gap_s: float = 1.2,
    cav_waiting_tiebreaker_weight: float = 0.0,
) -> AllocationDecision:
    if not vehicles:
        return AllocationDecision(release_order=[], hold_vehicles=[], scores={}, release_vehicles=[])

    if method == "fcfs":
        scores = {vehicle.veh_id: _fcfs_score(vehicle) for vehicle in vehicles}
    elif method in {"prediction_fcfs", "prediction_coalition"}:
        scores = {
            vehicle.veh_id: _prediction_coalition_score(
                vehicle,
                risk_threshold=risk_threshold,
                fairness_weight=fairness_weight if method == "prediction_coalition" else 0.0,
                hdv_priority_bonus=hdv_priority_bonus,
                cav_waiting_tiebreaker_weight=(
                    cav_waiting_tiebreaker_weight if method == "prediction_coalition" else 0.0
                ),
            )
            for vehicle in vehicles
        }
    else:
        raise ValueError(f"Unknown allocation method: {method}")

    ordered = sorted(
        vehicles,
        key=lambda item: (
            scores[item.veh_id],
            estimate_arrival_time(item),
            item.veh_id,
        ),
    )
    release_order = [vehicle.veh_id for vehicle in ordered]
    release_limit = release_count if max_release_count is None else max_release_count
    release_vehicles = _select_release_set(
        ordered=ordered,
        method=method,
        risk_threshold=risk_threshold,
        max_release_count=release_limit,
        safe_arrival_gap_s=safe_arrival_gap_s,
    )
    release_set = set(release_vehicles)
    hold_vehicles = [veh_id for veh_id in release_order if veh_id not in release_set]
    return AllocationDecision(
        release_order=release_order,
        hold_vehicles=hold_vehicles,
        scores=scores,
        release_vehicles=release_vehicles,
    )
