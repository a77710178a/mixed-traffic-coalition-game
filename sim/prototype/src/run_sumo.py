from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from common import PROTOTYPE_ROOT, distance, ensure_dirs, geometry_artifact_path, load_config, scenario_run_id, write_csv, write_json
from generate_network import generate_network
from generate_routes import build_routes


def ensure_traci() -> None:
    try:
        import traci  # noqa: F401
    except Exception as exc:
        raise RuntimeError("TraCI is required. Run this script inside the sumoenv environment.") from exc


def load_route_meta(route_dir: Path) -> dict:
    with (route_dir / "route_meta.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def read_junction_center(net_file: Path, junction_id: str = "C") -> tuple[float, float]:
    tree = ET.parse(net_file)
    for junction in tree.getroot().iter("junction"):
        if junction.attrib.get("id") == junction_id:
            return float(junction.attrib["x"]), float(junction.attrib["y"])
    raise ValueError(f"Junction {junction_id!r} not found in {net_file}")


def run_sumo(config_path: str, seed: int, volume: str, penetration: float, duration: float, gui: bool = False) -> dict[str, Path]:
    ensure_traci()
    import traci

    cfg = load_config(config_path)
    ensure_dirs()
    generate_network(config_path)
    geometry_path = geometry_artifact_path(cfg)
    build_routes(config_path, seed, volume, penetration, duration)
    rid = scenario_run_id(cfg, seed, volume, penetration)
    route_dir = PROTOTYPE_ROOT / "routes" / rid
    meta = load_route_meta(route_dir)

    log_dir = PROTOTYPE_ROOT / "logs" / rid
    log_dir.mkdir(parents=True, exist_ok=True)
    sumocfg = route_dir / "four_leg.sumocfg"
    center_x, center_y = read_junction_center(PROTOTYPE_ROOT / "networks" / "four_leg.net.xml")
    sumo_binary = "sumo-gui" if gui else "sumo"
    cmd = [sumo_binary, "-c", str(sumocfg), "--seed", str(seed), "--no-step-log", "true", "--duration-log.disable", "true"]

    route_meta = meta["route_meta"]
    rows = []
    traci.start(cmd)
    try:
        while traci.simulation.getTime() <= float(duration) and traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            now = float(traci.simulation.getTime())
            for veh_id in traci.vehicle.getIDList():
                x, y = traci.vehicle.getPosition(veh_id)
                route_id = traci.vehicle.getRouteID(veh_id)
                veh_type = traci.vehicle.getTypeID(veh_id)
                accel = traci.vehicle.getAcceleration(veh_id)
                speed = traci.vehicle.getSpeed(veh_id)
                angle = traci.vehicle.getAngle(veh_id)
                route_info = route_meta.get(route_id, {})
                rows.append({
                    "time": f"{now:.2f}",
                    "veh_id": veh_id,
                    "veh_class": "CAV" if veh_type == "CAV" else "HDV",
                    "veh_type": veh_type,
                    "route_id": route_id,
                    "origin": route_info.get("origin", ""),
                    "destination": route_info.get("destination", ""),
                    "movement": route_info.get("movement", ""),
                    "lane_id": traci.vehicle.getLaneID(veh_id),
                    "x": f"{x:.3f}",
                    "y": f"{y:.3f}",
                    "speed": f"{speed:.3f}",
                    "acceleration": f"{accel:.3f}",
                    "heading": f"{angle:.3f}",
                    "distance_to_center": f"{distance(x, y, center_x, center_y):.3f}",
                })
    finally:
        traci.close()

    states_file = log_dir / "vehicle_states.csv"
    fields = [
        "time", "veh_id", "veh_class", "veh_type", "route_id", "origin", "destination", "movement",
        "lane_id", "x", "y", "speed", "acceleration", "heading", "distance_to_center",
    ]
    write_csv(states_file, rows, fields)
    run_meta = {
        "run_id": rid,
        "seed": seed,
        "volume": volume,
        "penetration": penetration,
        "duration": duration,
        "conflict_center_x": center_x,
        "conflict_center_y": center_y,
        "geometry_mode": cfg.get("geometry_mode", "center_debug"),
        "geometry_artifact": str(geometry_path) if geometry_path.exists() else "",
        "state_rows": len(rows),
        "vehicle_count": len({row["veh_id"] for row in rows}),
    }
    meta_file = log_dir / "run_meta.json"
    write_json(meta_file, run_meta)
    return {"states": states_file, "metadata": meta_file}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(PROTOTYPE_ROOT / "config" / "default_scenario.json"))
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--volume", choices=["low", "medium", "high"], default="low")
    parser.add_argument("--penetration", type=float, default=0.5)
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args()
    outputs = run_sumo(args.config, args.seed, args.volume, args.penetration, args.duration, args.gui)
    for key, path in outputs.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
