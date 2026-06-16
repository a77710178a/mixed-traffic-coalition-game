from __future__ import annotations

import argparse
from collections import defaultdict

from common import PROTOTYPE_ROOT, ensure_dirs, load_config, read_csv, write_csv, write_json


def extract_events(config_path: str, run_id_value: str) -> dict:
    cfg = load_config(config_path)
    ensure_dirs()
    states_file = PROTOTYPE_ROOT / "logs" / run_id_value / "vehicle_states.csv"
    rows = read_csv(states_file)
    zone = cfg["conflict_zones"][0]
    radius = float(zone["radius_m"])
    zone_id = zone["zone_id"]

    by_vehicle: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_vehicle[row["veh_id"]].append(row)

    events = []
    for veh_id, veh_rows in by_vehicle.items():
        veh_rows.sort(key=lambda r: float(r["time"]))
        inside = [r for r in veh_rows if float(r["distance_to_center"]) <= radius]
        if not inside:
            continue
        entry = inside[0]
        exit_row = inside[-1]
        pre_rows = [r for r in veh_rows if float(entry["time"]) - 3.0 <= float(r["time"]) <= float(entry["time"])]
        min_accel = min((float(r["acceleration"]) for r in pre_rows), default=0.0)
        min_speed = min((float(r["speed"]) for r in pre_rows), default=0.0)
        events.append({
            "veh_id": veh_id,
            "veh_class": entry["veh_class"],
            "veh_type": entry["veh_type"],
            "route_id": entry["route_id"],
            "origin": entry["origin"],
            "destination": entry["destination"],
            "movement": entry["movement"],
            "zone_id": zone_id,
            "entry_time": entry["time"],
            "exit_time": exit_row["time"],
            "min_pre_zone_accel": f"{min_accel:.3f}",
            "min_pre_zone_speed": f"{min_speed:.3f}",
        })

    out_file = PROTOTYPE_ROOT / "logs" / run_id_value / "conflict_events.csv"
    fields = [
        "veh_id", "veh_class", "veh_type", "route_id", "origin", "destination", "movement", "zone_id",
        "entry_time", "exit_time", "min_pre_zone_accel", "min_pre_zone_speed",
    ]
    write_csv(out_file, events, fields)
    summary = {
        "run_id": run_id_value,
        "event_count": len(events),
        "hdv_event_count": sum(1 for e in events if e["veh_class"] == "HDV"),
        "cav_event_count": sum(1 for e in events if e["veh_class"] == "CAV"),
    }
    summary_file = PROTOTYPE_ROOT / "reports" / f"{run_id_value}_events_summary.json"
    write_json(summary_file, summary)
    return {"events": str(out_file), "summary": str(summary_file), **summary}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(PROTOTYPE_ROOT / "config" / "default_scenario.json"))
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    outputs = extract_events(args.config, args.run_id)
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

