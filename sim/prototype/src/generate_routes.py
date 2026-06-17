from __future__ import annotations

import argparse
import random
import xml.etree.ElementTree as ET
from pathlib import Path

from common import (
    PROTOTYPE_ROOT,
    ensure_dirs,
    load_config,
    scenario_run_id,
    weighted_choice,
    write_json,
)
from generate_network import write_xml
from topology import active_approaches, allowed_turn_weights, route_specs


def build_routes(config_path: str, seed: int, volume: str, penetration: float, duration: float) -> dict[str, Path]:
    cfg = load_config(config_path)
    ensure_dirs()
    rng = random.Random(seed)
    rid = scenario_run_id(cfg, seed, volume, penetration)
    route_dir = PROTOTYPE_ROOT / "routes" / rid
    route_dir.mkdir(parents=True, exist_ok=True)
    approaches = active_approaches(cfg)
    specs = route_specs(approaches)

    root = ET.Element("routes")
    ET.SubElement(root, "vType", id="CAV", vClass="passenger", color="0,180,255", accel="2.6", decel="4.0", tau="0.8", minGap="2.0", sigma="0.1")
    for profile, params in cfg["hdv_behavior_profiles"].items():
        ET.SubElement(
            root,
            "vType",
            id=f"HDV_{profile}",
            vClass="passenger",
            color="255,180,0",
            accel=str(params["accel"]),
            decel=str(params["decel"]),
            tau=str(params["tau"]),
            minGap=str(params["minGap"]),
            sigma=str(params["sigma"]),
        )

    route_meta: dict[str, dict] = {}
    for spec in specs:
        ET.SubElement(root, "route", id=spec.route_id, edges=spec.edges)
        route_meta[spec.route_id] = {
            "origin": spec.origin,
            "destination": spec.destination,
            "movement": spec.movement,
        }

    demand_per_approach = float(cfg["traffic_volumes_veh_per_hour_per_approach"][volume])
    expected_total = demand_per_approach * len(approaches) * duration / 3600.0
    vehicle_count = max(1, int(round(expected_total)))
    turn_weights = cfg["turning_ratio"]
    hdv_mix = cfg["hdv_behavior_mix"]
    turn_weights_by_origin = {
        origin: allowed_turn_weights(origin, approaches, turn_weights)
        for origin in approaches
    }

    vehicles = []
    for index in range(vehicle_count):
        depart = rng.random() * float(duration)
        origin = rng.choice(list(approaches))
        movement = weighted_choice(rng, turn_weights_by_origin[origin])
        route = f"r_{origin}_{movement}"
        is_cav = rng.random() < float(penetration)
        if is_cav:
            veh_type = "CAV"
            behavior = "controlled"
        else:
            behavior = weighted_choice(rng, hdv_mix)
            veh_type = f"HDV_{behavior}"
        veh_id = f"{veh_type}_{index:05d}"
        vehicles.append((depart, veh_id, veh_type, route))

    for depart, veh_id, veh_type, route in sorted(vehicles, key=lambda item: item[0]):
        ET.SubElement(
            root,
            "vehicle",
            id=veh_id,
            type=veh_type,
            route=route,
            depart=f"{depart:.2f}",
            departLane="best",
            departSpeed="max",
        )

    route_file = route_dir / "four_leg.rou.xml"
    cfg_file = route_dir / "four_leg.sumocfg"
    write_xml(route_file, root)

    sumocfg = ET.Element("configuration")
    input_el = ET.SubElement(sumocfg, "input")
    ET.SubElement(input_el, "net-file", value=str(PROTOTYPE_ROOT / "networks" / "four_leg.net.xml"))
    ET.SubElement(input_el, "route-files", value=str(route_file))
    time_el = ET.SubElement(sumocfg, "time")
    ET.SubElement(time_el, "begin", value="0")
    ET.SubElement(time_el, "end", value=str(duration))
    ET.SubElement(time_el, "step-length", value=str(cfg["step_length"]))
    processing_el = ET.SubElement(sumocfg, "processing")
    ET.SubElement(processing_el, "collision.action", value="warn")
    ET.SubElement(processing_el, "time-to-teleport", value="-1")
    write_xml(cfg_file, sumocfg)

    meta = {
        "run_id": rid,
        "active_approaches": list(approaches),
        "seed": seed,
        "volume": volume,
        "penetration": penetration,
        "duration": duration,
        "vehicle_count": vehicle_count,
        "route_meta": route_meta,
    }
    meta_file = route_dir / "route_meta.json"
    write_json(meta_file, meta)
    return {"routes": route_file, "sumocfg": cfg_file, "metadata": meta_file}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(PROTOTYPE_ROOT / "config" / "default_scenario.json"))
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--volume", choices=["low", "medium", "high"], default="low")
    parser.add_argument("--penetration", type=float, default=0.5)
    parser.add_argument("--duration", type=float, default=120.0)
    args = parser.parse_args()
    outputs = build_routes(args.config, args.seed, args.volume, args.penetration, args.duration)
    for key, path in outputs.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
