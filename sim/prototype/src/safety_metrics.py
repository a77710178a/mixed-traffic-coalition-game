from __future__ import annotations

import argparse
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

from common import PROTOTYPE_ROOT, movement_to_destination, read_csv, write_csv, write_json


@dataclass(frozen=True)
class ZoneOccupancy:
    veh_id: str
    veh_class: str
    origin: str
    destination: str
    movement: str
    entry_time: float
    exit_time: float


APPROACH_POINTS = {
    "N": (0.0, 1.0),
    "E": (1.0, 0.0),
    "S": (0.0, -1.0),
    "W": (-1.0, 0.0),
}


def _float(row: dict, key: str) -> float:
    return float(row.get(key, 0.0))


def _vehicle_key(row: dict) -> str:
    return str(row.get("veh_id", ""))


def extract_zone_occupancies(rows: list[dict], zone_radius_m: float) -> list[ZoneOccupancy]:
    by_vehicle: dict[str, list[dict]] = {}
    for row in rows:
        veh_id = _vehicle_key(row)
        if not veh_id:
            continue
        by_vehicle.setdefault(veh_id, []).append(row)

    occupancies = []
    for veh_id, vehicle_rows in by_vehicle.items():
        vehicle_rows.sort(key=lambda item: _float(item, "time"))
        active_rows: list[dict] = []
        for row in vehicle_rows:
            inside = _float(row, "distance_to_center") <= zone_radius_m
            if inside:
                active_rows.append(row)
            elif active_rows:
                occupancies.append(_occupancy_from_rows(veh_id, active_rows, exit_row=row))
                active_rows = []
        if active_rows:
            occupancies.append(_occupancy_from_rows(veh_id, active_rows, exit_row=None))

    occupancies.sort(key=lambda item: (item.entry_time, item.exit_time, item.veh_id))
    return occupancies


def _occupancy_from_rows(veh_id: str, rows: list[dict], exit_row: dict | None) -> ZoneOccupancy:
    first = rows[0]
    last = exit_row or rows[-1]
    return ZoneOccupancy(
        veh_id=veh_id,
        veh_class=str(first.get("veh_class", "")),
        origin=str(first.get("origin", "")),
        destination=str(first.get("destination", "")),
        movement=str(first.get("movement", "")),
        entry_time=_float(first, "time"),
        exit_time=_float(last, "time"),
    )


def _is_conflicting_pair(a: ZoneOccupancy, b: ZoneOccupancy) -> bool:
    if a.veh_id == b.veh_id:
        return False
    if a.origin and b.origin and a.origin == b.origin:
        return False
    return movements_conflict(a.origin, a.movement, a.destination, b.origin, b.movement, b.destination)


def _destination(origin: str, movement: str, destination: str) -> str:
    if destination:
        return destination
    if not origin or not movement:
        return ""
    try:
        return movement_to_destination(origin, movement)
    except Exception:
        return ""


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_intersect(
    a1: tuple[float, float],
    a2: tuple[float, float],
    b1: tuple[float, float],
    b2: tuple[float, float],
) -> bool:
    o1 = _orientation(a1, a2, b1)
    o2 = _orientation(a1, a2, b2)
    o3 = _orientation(b1, b2, a1)
    o4 = _orientation(b1, b2, a2)
    return o1 * o2 <= 0.0 and o3 * o4 <= 0.0


def movements_conflict(
    origin_a: str,
    movement_a: str,
    destination_a: str,
    origin_b: str,
    movement_b: str,
    destination_b: str,
) -> bool:
    if origin_a == origin_b:
        return False
    dest_a = _destination(origin_a, movement_a, destination_a)
    dest_b = _destination(origin_b, movement_b, destination_b)
    if origin_a not in APPROACH_POINTS or origin_b not in APPROACH_POINTS:
        return True
    if dest_a not in APPROACH_POINTS or dest_b not in APPROACH_POINTS:
        return True
    a1, a2 = APPROACH_POINTS[origin_a], APPROACH_POINTS[dest_a]
    b1, b2 = APPROACH_POINTS[origin_b], APPROACH_POINTS[dest_b]
    if a1 in {b1, b2} or a2 in {b1, b2}:
        return False
    return _segments_intersect(a1, a2, b1, b2)


def _pet_seconds(a: ZoneOccupancy, b: ZoneOccupancy) -> float:
    first, second = (a, b) if a.entry_time <= b.entry_time else (b, a)
    return second.entry_time - first.exit_time


def compute_conflict_safety_metrics(
    rows: list[dict],
    zone_radius_m: float,
    near_conflict_pet_s: float,
) -> dict:
    occupancies = extract_zone_occupancies(rows, zone_radius_m=zone_radius_m)
    pets = []
    entry_gaps = []
    for a, b in combinations(occupancies, 2):
        if not _is_conflicting_pair(a, b):
            continue
        pets.append(_pet_seconds(a, b))
        entry_gaps.append(abs(a.entry_time - b.entry_time))

    near_conflicts = [pet for pet in pets if pet <= near_conflict_pet_s]
    return {
        "occupancy_count": len(occupancies),
        "conflict_pair_count": len(pets),
        "near_conflict_count": len(near_conflicts),
        "near_conflict_pet_threshold_s": near_conflict_pet_s,
        "min_pet_s": min(pets) if pets else None,
        "mean_pet_s": sum(pets) / len(pets) if pets else None,
        "min_entry_gap_s": min(entry_gaps) if entry_gaps else None,
    }


def occupancy_rows(occupancies: list[ZoneOccupancy]) -> list[dict]:
    return [
        {
            "veh_id": item.veh_id,
            "veh_class": item.veh_class,
            "origin": item.origin,
            "destination": item.destination,
            "movement": item.movement,
            "entry_time": f"{item.entry_time:.2f}",
            "exit_time": f"{item.exit_time:.2f}",
            "occupancy_duration_s": f"{max(0.0, item.exit_time - item.entry_time):.2f}",
        }
        for item in occupancies
    ]


def write_safety_outputs(
    states_csv: str | Path,
    output_dir: str | Path,
    zone_radius_m: float,
    near_conflict_pet_s: float,
) -> dict:
    rows = read_csv(states_csv)
    occupancies = extract_zone_occupancies(rows, zone_radius_m=zone_radius_m)
    metrics = compute_conflict_safety_metrics(
        rows,
        zone_radius_m=zone_radius_m,
        near_conflict_pet_s=near_conflict_pet_s,
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    occupancy_file = output_dir / "conflict_zone_occupancies.csv"
    metrics_file = output_dir / "safety_metrics.json"
    write_csv(
        occupancy_file,
        occupancy_rows(occupancies),
        ["veh_id", "veh_class", "origin", "destination", "movement", "entry_time", "exit_time", "occupancy_duration_s"],
    )
    write_json(metrics_file, metrics)
    return {"occupancies": str(occupancy_file), "metrics_file": str(metrics_file), **metrics}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--states-csv", required=True)
    parser.add_argument("--output-dir", default=str(PROTOTYPE_ROOT / "reports" / "safety_metrics"))
    parser.add_argument("--zone-radius-m", type=float, default=14.0)
    parser.add_argument("--near-conflict-pet-s", type=float, default=1.5)
    args = parser.parse_args()
    outputs = write_safety_outputs(
        states_csv=args.states_csv,
        output_dir=args.output_dir,
        zone_radius_m=args.zone_radius_m,
        near_conflict_pet_s=args.near_conflict_pet_s,
    )
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
