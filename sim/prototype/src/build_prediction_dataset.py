from __future__ import annotations

import argparse
import json
import math
from bisect import bisect_left
from collections import defaultdict
from pathlib import Path

from common import PROTOTYPE_ROOT, ensure_dirs, read_csv, write_json


STATE_KEYS = ["x", "y", "speed", "acceleration", "heading", "distance_to_center"]


def _float(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def _safe_time_to_center(distance: float, speed: float) -> float:
    return distance / max(speed, 0.1)


def _load_states(run_id_value: str) -> dict[str, dict]:
    state_file = PROTOTYPE_ROOT / "logs" / run_id_value / "vehicle_states.csv"
    by_vehicle: dict[str, list[dict]] = defaultdict(list)
    for row in read_csv(state_file):
        by_vehicle[row["veh_id"]].append(row)

    indexed = {}
    for veh_id, rows in by_vehicle.items():
        rows.sort(key=lambda item: _float(item, "time"))
        indexed[veh_id] = {
            "times": [_float(row, "time") for row in rows],
            "rows": rows,
        }
    return indexed


def _nearest_row(index: dict, target_time: float, tolerance_s: float) -> dict | None:
    times = index["times"]
    rows = index["rows"]
    pos = bisect_left(times, target_time)
    candidates = []
    if pos < len(times):
        candidates.append(pos)
    if pos > 0:
        candidates.append(pos - 1)
    if not candidates:
        return None
    best = min(candidates, key=lambda idx: abs(times[idx] - target_time))
    if abs(times[best] - target_time) > tolerance_s:
        return None
    return rows[best]


def _history(index: dict, sample_time: float, history_s: float, step_s: float, tolerance_s: float) -> list[dict] | None:
    steps = int(round(history_s / step_s)) + 1
    start_time = sample_time - history_s
    history_rows = []
    for k in range(steps):
        t = start_time + k * step_s
        row = _nearest_row(index, t, tolerance_s)
        if row is None:
            return None
        history_rows.append({
            "time": round(t, 3),
            **{key: _float(row, key) for key in STATE_KEYS},
        })
    return history_rows


def _state_vector(row: dict) -> dict:
    return {key: _float(row, key) for key in STATE_KEYS}


def _edge_features(hdv_row: dict, other_row: dict) -> dict:
    hdv_speed = _float(hdv_row, "speed")
    other_speed = _float(other_row, "speed")
    hdv_dist = _float(hdv_row, "distance_to_center")
    other_dist = _float(other_row, "distance_to_center")
    hdv_ttc = _safe_time_to_center(hdv_dist, hdv_speed)
    other_ttc = _safe_time_to_center(other_dist, other_speed)
    dx = _float(hdv_row, "x") - _float(other_row, "x")
    dy = _float(hdv_row, "y") - _float(other_row, "y")
    return {
        "relative_distance": math.hypot(dx, dy),
        "relative_speed_hdv_minus_other": hdv_speed - other_speed,
        "distance_to_center_hdv_minus_other": hdv_dist - other_dist,
        "estimated_ttcp_hdv": hdv_ttc,
        "estimated_ttcp_other": other_ttc,
        "estimated_ttcp_diff_hdv_minus_other": hdv_ttc - other_ttc,
        "same_movement": int(hdv_row.get("movement") == other_row.get("movement")),
        "other_is_cav": int(other_row.get("veh_class") == "CAV"),
    }


def build_prediction_dataset(
    run_id_value: str,
    history_s: float,
    sample_step_s: float,
    prediction_horizon_s: float,
    tolerance_s: float,
    high_confidence_only: bool,
) -> dict:
    ensure_dirs()
    labels_file = PROTOTYPE_ROOT / "labels" / f"{run_id_value}_yield_labels.csv"
    labels = read_csv(labels_file)
    states = _load_states(run_id_value)

    out_dir = PROTOTYPE_ROOT / "datasets" / run_id_value
    out_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = out_dir / "prediction_samples.jsonl"
    skipped = CounterLike()
    written = 0

    with out_jsonl.open("w", encoding="utf-8") as f:
        for label in labels:
            if high_confidence_only and label.get("label_confidence") != "high":
                skipped.add("low_confidence")
                continue
            hdv_id = label["target_hdv"]
            other_id = label["interacting_vehicle"]
            if hdv_id not in states or other_id not in states:
                skipped.add("missing_vehicle_state")
                continue

            first_entry = min(_float(label, "hdv_entry_time"), _float(label, "other_entry_time"))
            sample_time = first_entry - prediction_horizon_s
            if sample_time <= 0:
                skipped.add("sample_time_before_start")
                continue

            hdv_hist = _history(states[hdv_id], sample_time, history_s, sample_step_s, tolerance_s)
            other_hist = _history(states[other_id], sample_time, history_s, sample_step_s, tolerance_s)
            if hdv_hist is None or other_hist is None:
                skipped.add("incomplete_history")
                continue

            hdv_now = _nearest_row(states[hdv_id], sample_time, tolerance_s)
            other_now = _nearest_row(states[other_id], sample_time, tolerance_s)
            if hdv_now is None or other_now is None:
                skipped.add("missing_sample_state")
                continue

            sample = {
                "sample_id": f"{run_id_value}_{label['sample_id']}",
                "run_id": run_id_value,
                "sample_time": round(sample_time, 3),
                "history_s": history_s,
                "sample_step_s": sample_step_s,
                "prediction_horizon_s": prediction_horizon_s,
                "target_hdv": hdv_id,
                "interacting_vehicle": other_id,
                "interacting_vehicle_class": label.get("interacting_vehicle_class", ""),
                "zone_id": label.get("zone_id", ""),
                "hdv_entry_time": _float(label, "hdv_entry_time"),
                "other_entry_time": _float(label, "other_entry_time"),
                "entry_time_diff_other_minus_hdv": _float(label, "entry_time_diff_other_minus_hdv"),
                "label_confidence": label.get("label_confidence", ""),
                "labels": {
                    "hdv_takes_priority": int(label.get("hdv_takes_priority", 0)),
                    "strict_non_yield": int(label.get("strict_non_yield", label.get("non_yield", 0))),
                },
                "hdv_context": {
                    "origin": label.get("hdv_origin", ""),
                    "movement": label.get("hdv_movement", ""),
                    "state_at_sample_time": _state_vector(hdv_now),
                },
                "other_context": {
                    "origin": label.get("other_origin", ""),
                    "movement": label.get("other_movement", ""),
                    "state_at_sample_time": _state_vector(other_now),
                },
                "edge_features": _edge_features(hdv_now, other_now),
                "hdv_history": hdv_hist,
                "other_history": other_hist,
            }
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            written += 1

    summary = {
        "run_id": run_id_value,
        "input_labels": len(labels),
        "written_samples": written,
        "skipped": skipped.data,
        "history_s": history_s,
        "sample_step_s": sample_step_s,
        "prediction_horizon_s": prediction_horizon_s,
        "high_confidence_only": high_confidence_only,
        "output_jsonl": str(out_jsonl),
    }
    summary_file = out_dir / "prediction_dataset_summary.json"
    write_json(summary_file, summary)
    return summary


class CounterLike:
    def __init__(self) -> None:
        self.data: dict[str, int] = {}

    def add(self, key: str) -> None:
        self.data[key] = self.data.get(key, 0) + 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--history-s", type=float, default=3.0)
    parser.add_argument("--sample-step-s", type=float, default=0.5)
    parser.add_argument("--prediction-horizon-s", type=float, default=1.0)
    parser.add_argument("--tolerance-s", type=float, default=0.16)
    parser.add_argument("--high-confidence-only", action="store_true")
    args = parser.parse_args()
    summary = build_prediction_dataset(
        run_id_value=args.run_id,
        history_s=args.history_s,
        sample_step_s=args.sample_step_s,
        prediction_horizon_s=args.prediction_horizon_s,
        tolerance_s=args.tolerance_s,
        high_confidence_only=args.high_confidence_only,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
