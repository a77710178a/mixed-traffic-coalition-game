from __future__ import annotations

import argparse
from itertools import combinations

from common import PROTOTYPE_ROOT, ensure_dirs, load_config, read_csv, write_csv, write_json


PRIORITY_LABEL_CONFLICT_TYPES = {"crossing", "merging", "overlap_turning"}


def generate_labels(config_path: str, run_id_value: str) -> dict:
    cfg = load_config(config_path)
    ensure_dirs()
    thresholds = cfg["label_thresholds"]
    epsilon_t = float(thresholds["epsilon_t_s"])
    yield_decel = float(thresholds["yield_decel_mps2"])
    high_conf = float(thresholds["high_confidence_entry_diff_s"])
    pair_window = float(thresholds["pair_time_window_s"])

    events_file = PROTOTYPE_ROOT / "logs" / run_id_value / "conflict_events.csv"
    events = read_csv(events_file)
    labels = []
    sample_id = 0
    for a, b in combinations(events, 2):
        if a["zone_id"] != b["zone_id"]:
            continue
        route_ids = {item for item in str(a.get("zone_route_ids", "")).split("|") if item}
        conflict_type = a.get("conflict_type") or b.get("conflict_type") or ""
        if route_ids:
            if conflict_type not in PRIORITY_LABEL_CONFLICT_TYPES:
                continue
            if a["route_id"] not in route_ids or b["route_id"] not in route_ids:
                continue
        elif a["origin"] == b["origin"]:
            continue
        entry_a = float(a["entry_time"])
        entry_b = float(b["entry_time"])
        if abs(entry_a - entry_b) > pair_window:
            continue
        hdv_candidates = []
        if a["veh_class"] == "HDV":
            hdv_candidates.append((a, b))
        if b["veh_class"] == "HDV":
            hdv_candidates.append((b, a))
        for hdv, other in hdv_candidates:
            hdv_entry = float(hdv["entry_time"])
            other_entry = float(other["entry_time"])
            hdv_min_accel = float(hdv["min_pre_zone_accel"])
            hdv_takes_priority = int(hdv_entry + epsilon_t < other_entry)
            strict_non_yield = int(hdv_takes_priority and (hdv_min_accel > -yield_decel))
            entry_diff = other_entry - hdv_entry
            confidence = "high" if abs(entry_diff) > high_conf else "low"
            sample_id += 1
            labels.append({
                "sample_id": sample_id,
                "target_hdv": hdv["veh_id"],
                "interacting_vehicle": other["veh_id"],
                "interacting_vehicle_class": other["veh_class"],
                "zone_id": hdv["zone_id"],
                "hdv_entry_time": f"{hdv_entry:.2f}",
                "other_entry_time": f"{other_entry:.2f}",
                "entry_time_diff_other_minus_hdv": f"{entry_diff:.2f}",
                "hdv_min_pre_zone_accel": f"{hdv_min_accel:.3f}",
                "hdv_takes_priority": hdv_takes_priority,
                "strict_non_yield": strict_non_yield,
                "non_yield": strict_non_yield,
                "label_confidence": confidence,
                "hdv_origin": hdv["origin"],
                "hdv_movement": hdv["movement"],
                "other_origin": other["origin"],
                "other_movement": other["movement"],
            })

    out_file = PROTOTYPE_ROOT / "labels" / f"{run_id_value}_yield_labels.csv"
    fields = [
        "sample_id", "target_hdv", "interacting_vehicle", "interacting_vehicle_class", "zone_id",
        "hdv_entry_time", "other_entry_time", "entry_time_diff_other_minus_hdv", "hdv_min_pre_zone_accel",
        "hdv_takes_priority", "strict_non_yield", "non_yield", "label_confidence",
        "hdv_origin", "hdv_movement", "other_origin", "other_movement",
    ]
    write_csv(out_file, labels, fields)
    summary = {
        "run_id": run_id_value,
        "label_count": len(labels),
        "hdv_takes_priority_count": sum(1 for row in labels if int(row["hdv_takes_priority"]) == 1),
        "hdv_yields_by_priority_count": sum(1 for row in labels if int(row["hdv_takes_priority"]) == 0),
        "strict_non_yield_count": sum(1 for row in labels if int(row["strict_non_yield"]) == 1),
        "non_yield_count": sum(1 for row in labels if int(row["non_yield"]) == 1),
        "yield_count": sum(1 for row in labels if int(row["non_yield"]) == 0),
        "high_confidence_count": sum(1 for row in labels if row["label_confidence"] == "high"),
        "low_confidence_count": sum(1 for row in labels if row["label_confidence"] == "low"),
    }
    summary_file = PROTOTYPE_ROOT / "reports" / f"{run_id_value}_label_summary.json"
    write_json(summary_file, summary)
    return {"labels": str(out_file), "summary": str(summary_file), **summary}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(PROTOTYPE_ROOT / "config" / "default_scenario.json"))
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    outputs = generate_labels(args.config, args.run_id)
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
