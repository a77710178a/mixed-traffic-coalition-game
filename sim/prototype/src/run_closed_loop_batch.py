from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import PROTOTYPE_ROOT, ensure_dirs, write_csv, write_json
from run_closed_loop_allocation import run_closed_loop_allocation
from run_label_sanity_batch import parse_csv_list


SUMMARY_FIELDS = [
    "method",
    "seed",
    "volume",
    "penetration",
    "vehicle_count_seen",
    "throughput_arrived",
    "mean_observed_travel_time_s",
    "mean_max_waiting_time_s",
    "max_waiting_time_s",
    "stop_count_proxy",
    "fairness_gini_waiting",
    "min_pairwise_ttc_proxy_s",
    "occupancy_count",
    "conflict_pair_count",
    "near_conflict_count",
    "min_pet_s",
    "mean_pet_s",
    "min_entry_gap_s",
    "max_release_count",
    "safe_arrival_gap_s",
    "cav_waiting_tiebreaker_weight",
    "adaptive_release_enabled",
    "adaptive_max_release_count",
    "adaptive_min_conflict_arrival_gap_s",
    "adaptive_max_occupancy",
    "projected_min_pet_s",
    "priority_predictor_type",
    "state_rows",
    "decision_rows",
]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _numeric(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def aggregate_rows(rows: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(str(row["method"]), []).append(row)

    aggregated = []
    metric_names = [
        "vehicle_count_seen",
        "throughput_arrived",
        "mean_observed_travel_time_s",
        "mean_max_waiting_time_s",
        "max_waiting_time_s",
        "stop_count_proxy",
        "fairness_gini_waiting",
        "min_pairwise_ttc_proxy_s",
        "occupancy_count",
        "conflict_pair_count",
        "near_conflict_count",
        "min_pet_s",
        "mean_pet_s",
        "min_entry_gap_s",
    ]
    for method, method_rows in sorted(groups.items()):
        out = {"method": method, "run_count": len(method_rows)}
        for metric in metric_names:
            values = [_numeric(row.get(metric)) for row in method_rows]
            clean_values = [value for value in values if value is not None]
            out[f"{metric}_mean"] = _mean(clean_values)
        aggregated.append(out)
    return aggregated


def run_batch(
    config_path: str,
    seeds: list[int],
    volumes: list[str],
    penetrations: list[float],
    methods: list[str],
    duration: float,
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
    projected_min_pet_s: float = 0.0,
    near_conflict_pet_s: float = 1.5,
    priority_model: str | None = None,
    output_name: str = "closed_loop_pilot_seed7_9_low_medium_pen50",
) -> dict:
    ensure_dirs()
    out_dir = PROTOTYPE_ROOT / "reports" / output_name
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for seed in seeds:
        for volume in volumes:
            for penetration in penetrations:
                for method in methods:
                    summary = run_closed_loop_allocation(
                        config_path=config_path,
                        seed=seed,
                        volume=volume,
                        penetration=penetration,
                        duration=duration,
                        method=method,
                        control_radius_m=control_radius_m,
                        hold_speed_mps=hold_speed_mps,
                        risk_threshold=risk_threshold,
                        fairness_weight=fairness_weight,
                        max_release_count=max_release_count,
                        safe_arrival_gap_s=safe_arrival_gap_s,
                        cav_waiting_tiebreaker_weight=cav_waiting_tiebreaker_weight,
                        adaptive_release_enabled=adaptive_release_enabled,
                        adaptive_max_release_count=adaptive_max_release_count,
                        adaptive_min_conflict_arrival_gap_s=adaptive_min_conflict_arrival_gap_s,
                        adaptive_max_occupancy=adaptive_max_occupancy,
                        projected_min_pet_s=projected_min_pet_s,
                        near_conflict_pet_s=near_conflict_pet_s,
                        priority_model=priority_model,
                        gui=False,
                    )
                    rows.append({field: summary.get(field) for field in SUMMARY_FIELDS})

    runs_csv = out_dir / "closed_loop_batch_runs.csv"
    aggregate_csv = out_dir / "closed_loop_batch_aggregate.csv"
    summary_json = out_dir / "closed_loop_batch_summary.json"
    aggregate = aggregate_rows(rows)
    write_csv(runs_csv, rows, SUMMARY_FIELDS)
    aggregate_fields = ["method", "run_count"] + [field for field in aggregate[0] if field not in {"method", "run_count"}] if aggregate else ["method", "run_count"]
    write_csv(aggregate_csv, aggregate, aggregate_fields)
    payload = {
        "output_name": output_name,
        "config_path": config_path,
        "seeds": seeds,
        "volumes": volumes,
        "penetrations": penetrations,
        "methods": methods,
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
        "projected_min_pet_s": projected_min_pet_s,
        "near_conflict_pet_s": near_conflict_pet_s,
        "priority_model": priority_model or "",
        "run_count": len(rows),
        "runs_csv": str(runs_csv),
        "aggregate_csv": str(aggregate_csv),
        "aggregate": aggregate,
    }
    write_json(summary_json, payload)
    return {"summary": str(summary_json), "runs_csv": str(runs_csv), "aggregate_csv": str(aggregate_csv), **payload}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(PROTOTYPE_ROOT / "config" / "stress_scenario.json"))
    parser.add_argument("--seeds", default="7,8,9")
    parser.add_argument("--volumes", default="low,medium")
    parser.add_argument("--penetrations", default="0.5")
    parser.add_argument("--methods", default="fcfs,prediction_fcfs,prediction_coalition")
    parser.add_argument("--duration", type=float, default=120.0)
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
    parser.add_argument("--projected-min-pet-s", type=float, default=0.0)
    parser.add_argument("--near-conflict-pet-s", type=float, default=1.5)
    parser.add_argument("--priority-model", default=None)
    parser.add_argument("--output-name", default="closed_loop_pilot_seed7_9_low_medium_pen50")
    args = parser.parse_args()

    summary = run_batch(
        config_path=args.config,
        seeds=parse_csv_list(args.seeds, int),
        volumes=parse_csv_list(args.volumes, str),
        penetrations=parse_csv_list(args.penetrations, float),
        methods=parse_csv_list(args.methods, str),
        duration=args.duration,
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
        projected_min_pet_s=args.projected_min_pet_s,
        near_conflict_pet_s=args.near_conflict_pet_s,
        priority_model=args.priority_model,
        output_name=args.output_name,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
