from __future__ import annotations

import argparse
from collections import defaultdict

from common import PROTOTYPE_ROOT, ensure_dirs, geometry_artifact_path, load_config, read_csv, write_csv, write_json
from route_geometry import load_route_geometry


def _distance_xy(row: dict, centroid: dict, coordinate_origin: tuple[float, float]) -> float:
    x0, y0 = coordinate_origin
    dx = float(row["x"]) - x0 - float(centroid["x"])
    dy = float(row["y"]) - y0 - float(centroid["y"])
    return (dx * dx + dy * dy) ** 0.5


def extract_route_zone_events_from_rows(
    rows: list[dict],
    artifact: dict,
    pre_zone_window_s: float,
    coordinate_origin: tuple[float, float] = (0.0, 0.0),
) -> list[dict]:
    route_zones: dict[str, list[dict]] = defaultdict(list)
    for zone in artifact.get("zones", []):
        for route_id in zone.get("route_ids", []):
            route_zones[route_id].append(zone)

    by_vehicle: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_vehicle[row["veh_id"]].append(row)

    events = []
    for veh_id, veh_rows in by_vehicle.items():
        veh_rows.sort(key=lambda r: float(r["time"]))
        route_id = veh_rows[0].get("route_id", "")
        for zone in route_zones.get(route_id, []):
            inside = [
                r for r in veh_rows
                if _distance_xy(r, zone["centroid"], coordinate_origin) <= float(zone["radius_m"])
            ]
            if not inside:
                continue
            entry = inside[0]
            exit_row = inside[-1]
            pre_rows = [
                r for r in veh_rows
                if float(entry["time"]) - pre_zone_window_s <= float(r["time"]) <= float(entry["time"])
            ]
            min_accel = min((float(r.get("acceleration", 0.0)) for r in pre_rows), default=0.0)
            min_speed = min((float(r.get("speed", 0.0)) for r in pre_rows), default=0.0)
            events.append({
                "veh_id": veh_id,
                "veh_class": entry.get("veh_class", ""),
                "veh_type": entry.get("veh_type", ""),
                "route_id": route_id,
                "origin": entry.get("origin", ""),
                "destination": entry.get("destination", ""),
                "movement": entry.get("movement", ""),
                "zone_id": zone["zone_id"],
                "conflict_type": zone.get("conflict_type", "none"),
                "zone_route_ids": "|".join(zone.get("route_ids", [])),
                "entry_time": entry["time"],
                "exit_time": exit_row["time"],
                "min_pre_zone_accel": f"{min_accel:.3f}",
                "min_pre_zone_speed": f"{min_speed:.3f}",
            })
    events.sort(key=lambda item: (float(item["entry_time"]), item["veh_id"], item["zone_id"]))
    return events


def extract_events(config_path: str, run_id_value: str, states_file: str | None = None) -> dict:
    cfg = load_config(config_path)
    ensure_dirs()
    states_path = states_file or str(PROTOTYPE_ROOT / "logs" / run_id_value / "vehicle_states.csv")
    rows = read_csv(states_path)
    pre_zone_window = float(cfg["label_thresholds"].get("pre_zone_window_s", 3.0))
    geometry_mode = str(cfg.get("geometry_mode", "center_debug"))
    events: list[dict]
    if geometry_mode == "route_zones":
        artifact = load_route_geometry(geometry_artifact_path(cfg))
        meta_file = PROTOTYPE_ROOT / "logs" / run_id_value / "run_meta.json"
        coordinate_origin = (0.0, 0.0)
        if meta_file.exists():
            meta = load_config(meta_file)
            coordinate_origin = (float(meta.get("conflict_center_x", 0.0)), float(meta.get("conflict_center_y", 0.0)))
        events = extract_route_zone_events_from_rows(rows, artifact, pre_zone_window, coordinate_origin)
    else:
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
            pre_rows = [
                r for r in veh_rows
                if float(entry["time"]) - pre_zone_window <= float(r["time"]) <= float(entry["time"])
            ]
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
                "conflict_type": "center_debug",
                "zone_route_ids": "",
                "entry_time": entry["time"],
                "exit_time": exit_row["time"],
                "min_pre_zone_accel": f"{min_accel:.3f}",
                "min_pre_zone_speed": f"{min_speed:.3f}",
            })

    out_file = PROTOTYPE_ROOT / "logs" / run_id_value / "conflict_events.csv"
    fields = [
        "veh_id", "veh_class", "veh_type", "route_id", "origin", "destination", "movement",
        "zone_id", "conflict_type", "zone_route_ids", "entry_time", "exit_time",
        "min_pre_zone_accel", "min_pre_zone_speed",
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
