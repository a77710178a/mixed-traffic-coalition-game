from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from allocation_policy import VehicleState, build_decision, estimate_arrival_time, fairness_gini
from common import PROTOTYPE_ROOT, distance, ensure_dirs, geometry_artifact_path, load_config, scenario_run_id, write_csv, write_json
from extract_conflict_events import extract_events
from generate_network import generate_network
from generate_routes import build_routes
from priority_predictor import HeuristicPriorityPredictor, PriorityPredictor, load_priority_predictor
from route_geometry import load_route_geometry
from run_sumo import ensure_traci, load_route_meta, read_junction_center
from safety_metrics import write_safety_outputs


def _safe_float(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return float(value)


def _candidate_states(
    traci,
    center_x: float,
    center_y: float,
    control_radius_m: float,
    priority_predictor: PriorityPredictor,
    route_meta: dict,
) -> list[VehicleState]:
    candidates = []
    for veh_id in traci.vehicle.getIDList():
        x, y = traci.vehicle.getPosition(veh_id)
        dist = distance(x, y, center_x, center_y)
        if dist > control_radius_m:
            continue
        veh_type = traci.vehicle.getTypeID(veh_id)
        route_id = traci.vehicle.getRouteID(veh_id)
        route_info = route_meta.get(route_id, {})
        candidates.append(
            VehicleState(
                veh_id=veh_id,
                veh_class="CAV" if veh_type == "CAV" else "HDV",
                distance_to_center=dist,
                speed=max(0.0, _safe_float(traci.vehicle.getSpeed(veh_id))),
                waiting_time=max(0.0, _safe_float(traci.vehicle.getWaitingTime(veh_id))),
                route_id=route_id,
                origin=str(route_info.get("origin", "")),
                destination=str(route_info.get("destination", "")),
                movement=str(route_info.get("movement", "")),
            )
        )
    enriched = []
    for vehicle in candidates:
        enriched.append(
            VehicleState(
                veh_id=vehicle.veh_id,
                veh_class=vehicle.veh_class,
                distance_to_center=vehicle.distance_to_center,
                speed=vehicle.speed,
                waiting_time=vehicle.waiting_time,
                priority_probability=priority_predictor.predict(vehicle, candidates),
                route_id=vehicle.route_id,
                origin=vehicle.origin,
                destination=vehicle.destination,
                movement=vehicle.movement,
            )
        )
    return enriched


def _conflict_zone_occupancy(candidates: list[VehicleState], zone_radius_m: float) -> int:
    return sum(1 for vehicle in candidates if float(vehicle.distance_to_center) <= float(zone_radius_m))


def _apply_decision(
    traci,
    decision,
    candidates: list[VehicleState],
    hold_speed_mps: float,
    controlled_ids: set[str],
) -> dict[str, str]:
    candidate_by_id = {item.veh_id: item for item in candidates}
    actions = {}
    for veh_id, vehicle in candidate_by_id.items():
        if vehicle.veh_class.upper() != "CAV":
            continue
        controlled_ids.add(veh_id)
        if veh_id in decision.hold_vehicles:
            traci.vehicle.setSpeed(veh_id, hold_speed_mps)
            actions[veh_id] = "hold"
        else:
            traci.vehicle.setSpeed(veh_id, -1)
            actions[veh_id] = "release"
    for veh_id in list(controlled_ids):
        if veh_id not in candidate_by_id and veh_id in traci.vehicle.getIDList():
            traci.vehicle.setSpeed(veh_id, -1)
            controlled_ids.remove(veh_id)
    return actions


def _min_pairwise_ttc(candidates: list[VehicleState]) -> float | None:
    moving = [item for item in candidates if item.speed > 0.1]
    if len(moving) < 2:
        return None
    arrival_times = sorted(estimate_arrival_time(item) for item in moving)
    gaps = [b - a for a, b in zip(arrival_times, arrival_times[1:])]
    return min(gaps) if gaps else None


def run_closed_loop_allocation(
    config_path: str,
    seed: int,
    volume: str,
    penetration: float,
    duration: float,
    method: str,
    control_radius_m: float,
    hold_speed_mps: float,
    risk_threshold: float,
    fairness_weight: float,
    max_release_count: int,
    safe_arrival_gap_s: float,
    cav_waiting_tiebreaker_weight: float,
    adaptive_release_enabled: bool = False,
    adaptive_max_release_count: int | None = None,
    adaptive_min_conflict_arrival_gap_s: float = 2.4,
    adaptive_max_occupancy: int = 0,
    near_conflict_pet_s: float = 1.5,
    priority_model: str | None = None,
    gui: bool = False,
) -> dict[str, Path | str | float | int]:
    ensure_traci()
    import traci

    ensure_dirs()
    generate_network(config_path)
    build_routes(config_path, seed, volume, penetration, duration)
    cfg = load_config(config_path)
    geometry_path = geometry_artifact_path(cfg)
    rid = scenario_run_id(cfg, seed, volume, penetration)
    route_dir = PROTOTYPE_ROOT / "routes" / rid
    route_meta = load_route_meta(route_dir)["route_meta"]
    center_x, center_y = read_junction_center(PROTOTYPE_ROOT / "networks" / "four_leg.net.xml")
    route_conflict_matrix = None
    if cfg.get("geometry_mode") == "route_zones" and geometry_path.exists():
        route_conflict_matrix = load_route_geometry(geometry_path).get("conflict_matrix")
    priority_predictor = load_priority_predictor(priority_model)
    predictor_type = "heuristic" if isinstance(priority_predictor, HeuristicPriorityPredictor) else "logistic"

    output_name = f"{rid}_{method}"
    log_dir = PROTOTYPE_ROOT / "logs" / output_name
    log_dir.mkdir(parents=True, exist_ok=True)
    sumocfg = route_dir / "four_leg.sumocfg"
    sumo_binary = "sumo-gui" if gui else "sumo"
    cmd = [sumo_binary, "-c", str(sumocfg), "--seed", str(seed), "--no-step-log", "true", "--duration-log.disable", "true"]

    state_rows = []
    decision_rows = []
    first_seen: dict[str, float] = {}
    last_seen: dict[str, float] = {}
    waiting_by_vehicle: dict[str, float] = defaultdict(float)
    stop_steps_by_vehicle: dict[str, int] = defaultdict(int)
    completed_ids: set[str] = set()
    controlled_ids: set[str] = set()
    min_ttc_values = []

    traci.start(cmd)
    try:
        while traci.simulation.getTime() <= float(duration) and traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            now = float(traci.simulation.getTime())
            candidates = _candidate_states(traci, center_x, center_y, control_radius_m, priority_predictor, route_meta)
            zone_radius_m = float(cfg["conflict_zones"][0]["radius_m"])
            decision = build_decision(
                candidates,
                method=method,
                risk_threshold=risk_threshold,
                fairness_weight=fairness_weight,
                max_release_count=max_release_count,
                safe_arrival_gap_s=safe_arrival_gap_s,
                cav_waiting_tiebreaker_weight=cav_waiting_tiebreaker_weight,
                adaptive_release_enabled=adaptive_release_enabled,
                adaptive_max_release_count=adaptive_max_release_count,
                adaptive_min_conflict_arrival_gap_s=adaptive_min_conflict_arrival_gap_s,
                adaptive_max_occupancy=adaptive_max_occupancy,
                conflict_zone_occupancy=_conflict_zone_occupancy(candidates, zone_radius_m),
                route_conflict_matrix=route_conflict_matrix,
            )
            actions = _apply_decision(traci, decision, candidates, hold_speed_mps, controlled_ids)
            min_ttc = _min_pairwise_ttc(candidates)
            if min_ttc is not None:
                min_ttc_values.append(min_ttc)

            for veh_id in traci.simulation.getArrivedIDList():
                completed_ids.add(veh_id)

            for veh_id in traci.vehicle.getIDList():
                x, y = traci.vehicle.getPosition(veh_id)
                route_id = traci.vehicle.getRouteID(veh_id)
                veh_type = traci.vehicle.getTypeID(veh_id)
                speed = _safe_float(traci.vehicle.getSpeed(veh_id))
                waiting_time = _safe_float(traci.vehicle.getWaitingTime(veh_id))
                first_seen.setdefault(veh_id, now)
                last_seen[veh_id] = now
                waiting_by_vehicle[veh_id] = max(waiting_by_vehicle[veh_id], waiting_time)
                if speed < 0.2:
                    stop_steps_by_vehicle[veh_id] += 1
                route_info = route_meta.get(route_id, {})
                state_rows.append({
                    "time": f"{now:.2f}",
                    "veh_id": veh_id,
                    "veh_class": "CAV" if veh_type == "CAV" else "HDV",
                    "veh_type": veh_type,
                    "route_id": route_id,
                    "origin": route_info.get("origin", ""),
                    "destination": route_info.get("destination", ""),
                    "movement": route_info.get("movement", ""),
                    "x": f"{x:.3f}",
                    "y": f"{y:.3f}",
                    "speed": f"{speed:.3f}",
                    "waiting_time": f"{waiting_time:.3f}",
                    "distance_to_center": f"{distance(x, y, center_x, center_y):.3f}",
                    "control_action": actions.get(veh_id, ""),
                })

            if candidates:
                decision_rows.append({
                    "time": f"{now:.2f}",
                    "candidate_count": len(candidates),
                    "release_order": "|".join(decision.release_order),
                    "release_vehicles": "|".join(decision.release_vehicles or []),
                    "hold_vehicles": "|".join(decision.hold_vehicles),
                    "scores_json": json.dumps(decision.scores, sort_keys=True),
                })
    finally:
        traci.close()

    state_file = log_dir / "closed_loop_vehicle_states.csv"
    decision_file = log_dir / "allocation_decisions.csv"
    write_csv(
        state_file,
        state_rows,
        [
            "time", "veh_id", "veh_class", "veh_type", "route_id", "origin", "destination", "movement",
            "x", "y", "speed", "waiting_time", "distance_to_center", "control_action",
        ],
    )
    write_csv(
        decision_file,
        decision_rows,
        ["time", "candidate_count", "release_order", "release_vehicles", "hold_vehicles", "scores_json"],
    )
    write_json(
        log_dir / "run_meta.json",
        {
            "run_id": output_name,
            "base_run_id": rid,
            "seed": seed,
            "volume": volume,
            "penetration": penetration,
            "duration": duration,
            "conflict_center_x": center_x,
            "conflict_center_y": center_y,
            "geometry_mode": cfg.get("geometry_mode", "center_debug"),
            "geometry_artifact": str(geometry_path) if geometry_path.exists() else "",
            "state_rows": len(state_rows),
        },
    )
    zone_radius_m = float(cfg["conflict_zones"][0]["radius_m"])
    event_outputs = extract_events(config_path, output_name, states_file=str(state_file))
    safety = write_safety_outputs(
        states_csv=state_file,
        output_dir=log_dir,
        zone_radius_m=zone_radius_m,
        near_conflict_pet_s=near_conflict_pet_s,
        events_csv=event_outputs["events"],
        geometry_mode=str(cfg.get("geometry_mode", "center_debug")),
    )

    vehicle_ids = set(first_seen) | set(last_seen)
    travel_times = [last_seen[veh_id] - first_seen[veh_id] for veh_id in vehicle_ids if veh_id in last_seen]
    waiting_values = [waiting_by_vehicle[veh_id] for veh_id in vehicle_ids]
    step_length = float(cfg.get("step_length", 0.1))
    summary = {
        "run_id": rid,
        "output_name": output_name,
        "method": method,
        "seed": seed,
        "volume": volume,
        "penetration": penetration,
        "duration": duration,
        "control_radius_m": control_radius_m,
        "hold_speed_mps": hold_speed_mps,
        "risk_threshold": risk_threshold,
        "fairness_weight": fairness_weight,
        "max_release_count": max_release_count,
        "safe_arrival_gap_s": safe_arrival_gap_s,
        "cav_waiting_tiebreaker_weight": cav_waiting_tiebreaker_weight,
        "adaptive_release_enabled": adaptive_release_enabled,
        "adaptive_max_release_count": adaptive_max_release_count,
        "adaptive_min_conflict_arrival_gap_s": adaptive_min_conflict_arrival_gap_s,
        "adaptive_max_occupancy": adaptive_max_occupancy,
        "near_conflict_pet_s": near_conflict_pet_s,
        "priority_model": priority_model or "",
        "priority_predictor_type": predictor_type,
        "zone_radius_m": zone_radius_m,
        "geometry_mode": cfg.get("geometry_mode", "center_debug"),
        "geometry_artifact": str(geometry_path) if geometry_path.exists() else "",
        "conflict_events": event_outputs["events"],
        "vehicle_count_seen": len(vehicle_ids),
        "throughput_arrived": len(completed_ids),
        "mean_observed_travel_time_s": sum(travel_times) / len(travel_times) if travel_times else 0.0,
        "mean_max_waiting_time_s": sum(waiting_values) / len(waiting_values) if waiting_values else 0.0,
        "max_waiting_time_s": max(waiting_values) if waiting_values else 0.0,
        "stop_count_proxy": sum(1 for steps in stop_steps_by_vehicle.values() if steps * step_length >= 1.0),
        "fairness_gini_waiting": fairness_gini(waiting_values),
        "min_pairwise_ttc_proxy_s": min(min_ttc_values) if min_ttc_values else None,
        "occupancy_count": safety["occupancy_count"],
        "conflict_pair_count": safety["conflict_pair_count"],
        "near_conflict_count": safety["near_conflict_count"],
        "min_pet_s": safety["min_pet_s"],
        "mean_pet_s": safety["mean_pet_s"],
        "min_entry_gap_s": safety["min_entry_gap_s"],
        "state_rows": len(state_rows),
        "decision_rows": len(decision_rows),
        "states": str(state_file),
        "decisions": str(decision_file),
        "safety_metrics": safety["metrics_file"],
        "conflict_zone_occupancies": safety["occupancies"],
    }
    summary_file = PROTOTYPE_ROOT / "reports" / f"{output_name}_closed_loop_summary.json"
    write_json(summary_file, summary)
    return {"summary": summary_file, "states": state_file, "decisions": decision_file, **summary}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(PROTOTYPE_ROOT / "config" / "stress_scenario.json"))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--volume", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--penetration", type=float, default=0.5)
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--method", choices=["fcfs", "prediction_fcfs", "prediction_coalition"], default="fcfs")
    parser.add_argument("--control-radius-m", type=float, default=45.0)
    parser.add_argument("--hold-speed-mps", type=float, default=1.0)
    parser.add_argument("--risk-threshold", type=float, default=0.7)
    parser.add_argument("--fairness-weight", type=float, default=0.15)
    parser.add_argument("--max-release-count", type=int, default=3)
    parser.add_argument("--safe-arrival-gap-s", type=float, default=1.2)
    parser.add_argument("--cav-waiting-tiebreaker-weight", type=float, default=0.0)
    parser.add_argument("--adaptive-release-enabled", nargs="?", const="true", default="false", choices=["true", "false"])
    parser.add_argument("--adaptive-max-release-count", type=int, default=None)
    parser.add_argument("--adaptive-min-conflict-arrival-gap-s", type=float, default=2.4)
    parser.add_argument("--adaptive-max-occupancy", type=int, default=0)
    parser.add_argument("--near-conflict-pet-s", type=float, default=1.5)
    parser.add_argument("--priority-model", default=None)
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args()
    outputs = run_closed_loop_allocation(
        config_path=args.config,
        seed=args.seed,
        volume=args.volume,
        penetration=args.penetration,
        duration=args.duration,
        method=args.method,
        control_radius_m=args.control_radius_m,
        hold_speed_mps=args.hold_speed_mps,
        risk_threshold=args.risk_threshold,
        fairness_weight=args.fairness_weight,
        max_release_count=args.max_release_count,
        safe_arrival_gap_s=args.safe_arrival_gap_s,
        cav_waiting_tiebreaker_weight=args.cav_waiting_tiebreaker_weight,
        adaptive_release_enabled=args.adaptive_release_enabled == "true",
        adaptive_max_release_count=args.adaptive_max_release_count,
        adaptive_min_conflict_arrival_gap_s=args.adaptive_min_conflict_arrival_gap_s,
        adaptive_max_occupancy=args.adaptive_max_occupancy,
        near_conflict_pet_s=args.near_conflict_pet_s,
        priority_model=args.priority_model,
        gui=args.gui,
    )
    print(json.dumps({key: str(value) if isinstance(value, Path) else value for key, value in outputs.items()}, indent=2))


if __name__ == "__main__":
    main()
