from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_prediction_dataset import (
    STATE_KEYS,
    _edge_features,
    _float,
    _history,
    _load_states,
    _nearest_row,
)
from common import PROTOTYPE_ROOT, ensure_dirs, read_csv, write_json
from run_label_sanity_batch import parse_csv_list


def _label_key(label: dict) -> tuple[str, str, float]:
    return (
        label["target_hdv"],
        label["zone_id"],
        round(min(_float(label, "hdv_entry_time"), _float(label, "other_entry_time")), 2),
    )


def _state_distance(row: dict) -> float:
    return _float(row, "distance_to_center")


def _candidate_neighbors(
    states: dict[str, dict],
    target_id: str,
    sample_time: float,
    tolerance_s: float,
    conflict_radius_m: float,
) -> list[tuple[str, dict, dict]]:
    candidates = []
    target_now = _nearest_row(states[target_id], sample_time, tolerance_s)
    if target_now is None:
        return candidates
    for veh_id, index in states.items():
        if veh_id == target_id:
            continue
        row = _nearest_row(index, sample_time, tolerance_s)
        if row is None:
            continue
        if _state_distance(row) > conflict_radius_m:
            continue
        edge = _edge_features(target_now, row)
        candidates.append((veh_id, row, edge))
    candidates.sort(key=lambda item: float(item[2]["relative_distance"]))
    return candidates


def build_graph_dataset_for_run(
    run_id_value: str,
    history_s: float,
    sample_step_s: float,
    prediction_horizon_s: float,
    tolerance_s: float,
    high_confidence_only: bool,
    max_neighbors: int,
    conflict_radius_m: float,
    min_neighbors: int,
    output_name: str,
) -> dict:
    ensure_dirs()
    labels_file = PROTOTYPE_ROOT / "labels" / f"{run_id_value}_yield_labels.csv"
    labels = read_csv(labels_file)
    states = _load_states(run_id_value)

    seen_keys = set()
    out_dir = PROTOTYPE_ROOT / "graph_datasets" / output_name / run_id_value
    out_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = out_dir / "graph_prediction_samples.jsonl"
    skipped: dict[str, int] = {}
    written = 0

    def skip(reason: str) -> None:
        skipped[reason] = skipped.get(reason, 0) + 1

    with out_jsonl.open("w", encoding="utf-8") as f:
        for label in labels:
            if high_confidence_only and label.get("label_confidence") != "high":
                skip("low_confidence")
                continue
            sample_key = _label_key(label)
            if sample_key in seen_keys:
                skip("duplicate_target_event")
                continue
            seen_keys.add(sample_key)

            target_id = label["target_hdv"]
            if target_id not in states:
                skip("missing_target_state")
                continue
            first_entry = min(_float(label, "hdv_entry_time"), _float(label, "other_entry_time"))
            sample_time = first_entry - prediction_horizon_s
            if sample_time <= 0:
                skip("sample_time_before_start")
                continue
            target_history = _history(states[target_id], sample_time, history_s, sample_step_s, tolerance_s)
            target_now = _nearest_row(states[target_id], sample_time, tolerance_s)
            if target_history is None or target_now is None:
                skip("incomplete_target_history")
                continue

            neighbors = []
            for neighbor_id, neighbor_now, edge in _candidate_neighbors(
                states=states,
                target_id=target_id,
                sample_time=sample_time,
                tolerance_s=tolerance_s,
                conflict_radius_m=conflict_radius_m,
            )[:max_neighbors]:
                neighbor_history = _history(states[neighbor_id], sample_time, history_s, sample_step_s, tolerance_s)
                if neighbor_history is None:
                    continue
                neighbors.append({
                    "veh_id": neighbor_id,
                    "veh_class": neighbor_now.get("veh_class", ""),
                    "movement": neighbor_now.get("movement", ""),
                    "state_at_sample_time": {key: _float(neighbor_now, key) for key in STATE_KEYS},
                    "edge_features": edge,
                    "history": neighbor_history,
                })
            if len(neighbors) < min_neighbors:
                skip("too_few_neighbors")
                continue

            sample = {
                "sample_id": f"{run_id_value}_graph_{written + 1}",
                "source_pair_sample_id": label["sample_id"],
                "run_id": run_id_value,
                "sample_time": round(sample_time, 3),
                "history_s": history_s,
                "sample_step_s": sample_step_s,
                "prediction_horizon_s": prediction_horizon_s,
                "target_hdv": target_id,
                "zone_id": label.get("zone_id", ""),
                "label_confidence": label.get("label_confidence", ""),
                "labels": {
                    "hdv_takes_priority": int(label.get("hdv_takes_priority", 0)),
                    "strict_non_yield": int(label.get("strict_non_yield", label.get("non_yield", 0))),
                },
                "target_context": {
                    "origin": label.get("hdv_origin", ""),
                    "movement": label.get("hdv_movement", ""),
                    "state_at_sample_time": {key: _float(target_now, key) for key in STATE_KEYS},
                },
                "target_history": target_history,
                "neighbors": neighbors,
            }
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            written += 1

    summary = {
        "run_id": run_id_value,
        "input_labels": len(labels),
        "written_samples": written,
        "skipped": skipped,
        "history_s": history_s,
        "sample_step_s": sample_step_s,
        "prediction_horizon_s": prediction_horizon_s,
        "high_confidence_only": high_confidence_only,
        "max_neighbors": max_neighbors,
        "conflict_radius_m": conflict_radius_m,
        "min_neighbors": min_neighbors,
        "output_jsonl": str(out_jsonl),
    }
    write_json(out_dir / "graph_prediction_dataset_summary.json", summary)
    return summary


def build_graph_dataset_batch(
    seeds: list[int],
    volumes: list[str],
    penetrations: list[float],
    history_s: float,
    sample_step_s: float,
    prediction_horizon_s: float,
    tolerance_s: float,
    high_confidence_only: bool,
    max_neighbors: int,
    conflict_radius_m: float,
    min_neighbors: int,
    output_name: str,
) -> dict:
    ensure_dirs()
    out_dir = PROTOTYPE_ROOT / "graph_datasets" / output_name
    out_dir.mkdir(parents=True, exist_ok=True)
    merged_jsonl = out_dir / "graph_prediction_samples.jsonl"
    summaries = []
    total_samples = 0
    positive = 0
    strict_positive = 0
    with merged_jsonl.open("w", encoding="utf-8") as merged:
        for seed in seeds:
            for volume in volumes:
                for penetration in penetrations:
                    rid = f"seed{seed}_{volume}_pen{int(round(penetration * 100))}"
                    summary = build_graph_dataset_for_run(
                        run_id_value=rid,
                        history_s=history_s,
                        sample_step_s=sample_step_s,
                        prediction_horizon_s=prediction_horizon_s,
                        tolerance_s=tolerance_s,
                        high_confidence_only=high_confidence_only,
                        max_neighbors=max_neighbors,
                        conflict_radius_m=conflict_radius_m,
                        min_neighbors=min_neighbors,
                        output_name=output_name,
                    )
                    summaries.append(summary)
                    with Path(summary["output_jsonl"]).open("r", encoding="utf-8") as src:
                        for line in src:
                            merged.write(line)
                            obj = json.loads(line)
                            total_samples += 1
                            positive += int(obj["labels"]["hdv_takes_priority"])
                            strict_positive += int(obj["labels"]["strict_non_yield"])
    batch_summary = {
        "output_name": output_name,
        "run_count": len(summaries),
        "total_samples": total_samples,
        "hdv_takes_priority_count": positive,
        "hdv_takes_priority_ratio": positive / total_samples if total_samples else 0.0,
        "strict_non_yield_count": strict_positive,
        "strict_non_yield_ratio": strict_positive / total_samples if total_samples else 0.0,
        "merged_jsonl": str(merged_jsonl),
        "runs": summaries,
    }
    write_json(out_dir / "graph_prediction_dataset_batch_summary.json", batch_summary)
    return batch_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="5,6")
    parser.add_argument("--volumes", default="low,medium,high")
    parser.add_argument("--penetrations", default="0.2,0.5,0.8")
    parser.add_argument("--history-s", type=float, default=3.0)
    parser.add_argument("--sample-step-s", type=float, default=0.5)
    parser.add_argument("--prediction-horizon-s", type=float, default=3.0)
    parser.add_argument("--tolerance-s", type=float, default=0.16)
    parser.add_argument("--high-confidence-only", action="store_true")
    parser.add_argument("--max-neighbors", type=int, default=6)
    parser.add_argument("--conflict-radius-m", type=float, default=90.0)
    parser.add_argument("--min-neighbors", type=int, default=1)
    parser.add_argument("--output-name", default="stress_seed5_6_graph_hc_h3")
    args = parser.parse_args()
    summary = build_graph_dataset_batch(
        seeds=parse_csv_list(args.seeds, int),
        volumes=parse_csv_list(args.volumes, str),
        penetrations=parse_csv_list(args.penetrations, float),
        history_s=args.history_s,
        sample_step_s=args.sample_step_s,
        prediction_horizon_s=args.prediction_horizon_s,
        tolerance_s=args.tolerance_s,
        high_confidence_only=args.high_confidence_only,
        max_neighbors=args.max_neighbors,
        conflict_radius_m=args.conflict_radius_m,
        min_neighbors=args.min_neighbors,
        output_name=args.output_name,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
