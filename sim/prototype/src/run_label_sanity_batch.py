from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from common import PROTOTYPE_ROOT, ensure_dirs, run_id, write_csv, write_json
from extract_conflict_events import extract_events
from generate_yield_labels import generate_labels
from run_sumo import run_sumo


def parse_csv_list(raw: str, cast=str) -> list:
    return [cast(item.strip()) for item in raw.split(",") if item.strip()]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_batch(
    config_path: str,
    seeds: list[int],
    volumes: list[str],
    penetrations: list[float],
    duration: float,
    max_runs: int | None = None,
) -> dict:
    ensure_dirs()
    rows = []
    run_counter = 0
    for seed in seeds:
        for volume in volumes:
            for penetration in penetrations:
                if max_runs is not None and run_counter >= max_runs:
                    break
                rid = run_id(seed, volume, penetration)
                print(f"[batch] start {rid}", flush=True)
                run_sumo(config_path, seed, volume, penetration, duration, gui=False)
                event_result = extract_events(config_path, rid)
                label_result = generate_labels(config_path, rid)
                run_meta = load_json(PROTOTYPE_ROOT / "logs" / rid / "run_meta.json")
                rows.append({
                    "run_id": rid,
                    "seed": seed,
                    "volume": volume,
                    "penetration": penetration,
                    "duration": duration,
                    "vehicle_count": run_meta.get("vehicle_count", 0),
                    "state_rows": run_meta.get("state_rows", 0),
                    "event_count": event_result.get("event_count", 0),
                    "hdv_event_count": event_result.get("hdv_event_count", 0),
                    "cav_event_count": event_result.get("cav_event_count", 0),
                    "label_count": label_result.get("label_count", 0),
                    "non_yield_count": label_result.get("non_yield_count", 0),
                    "yield_count": label_result.get("yield_count", 0),
                    "high_confidence_count": label_result.get("high_confidence_count", 0),
                    "low_confidence_count": label_result.get("low_confidence_count", 0),
                })
                run_counter += 1
            if max_runs is not None and run_counter >= max_runs:
                break
        if max_runs is not None and run_counter >= max_runs:
            break

    report_dir = PROTOTYPE_ROOT / "reports"
    out_csv = report_dir / "label_sanity_batch_summary.csv"
    fields = [
        "run_id", "seed", "volume", "penetration", "duration", "vehicle_count", "state_rows",
        "event_count", "hdv_event_count", "cav_event_count", "label_count", "non_yield_count",
        "yield_count", "high_confidence_count", "low_confidence_count",
    ]
    write_csv(out_csv, rows, fields)
    totals = {
        "run_count": len(rows),
        "vehicle_count": sum(int(row["vehicle_count"]) for row in rows),
        "event_count": sum(int(row["event_count"]) for row in rows),
        "label_count": sum(int(row["label_count"]) for row in rows),
        "non_yield_count": sum(int(row["non_yield_count"]) for row in rows),
        "yield_count": sum(int(row["yield_count"]) for row in rows),
        "high_confidence_count": sum(int(row["high_confidence_count"]) for row in rows),
        "low_confidence_count": sum(int(row["low_confidence_count"]) for row in rows),
    }
    totals["non_yield_ratio"] = (
        totals["non_yield_count"] / totals["label_count"] if totals["label_count"] else 0.0
    )
    out_json = report_dir / "label_sanity_batch_summary.json"
    write_json(out_json, {"totals": totals, "runs": rows})
    return {"summary_csv": str(out_csv), "summary_json": str(out_json), "totals": totals}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(PROTOTYPE_ROOT / "config" / "default_scenario.json"))
    parser.add_argument("--seeds", default="1,2,3")
    parser.add_argument("--volumes", default="low,medium,high")
    parser.add_argument("--penetrations", default="0.5")
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--max-runs", type=int, default=None)
    args = parser.parse_args()
    result = run_batch(
        config_path=args.config,
        seeds=parse_csv_list(args.seeds, int),
        volumes=parse_csv_list(args.volumes, str),
        penetrations=parse_csv_list(args.penetrations, float),
        duration=args.duration,
        max_runs=args.max_runs,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

