from __future__ import annotations

import csv
import json
import math
import random
from pathlib import Path
from typing import Iterable


PROTOTYPE_ROOT = Path(__file__).resolve().parents[1]


def load_config(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dirs() -> None:
    for name in ["networks", "routes", "configs", "logs", "labels", "reports"]:
        (PROTOTYPE_ROOT / name).mkdir(parents=True, exist_ok=True)


def run_id(seed: int, volume: str, penetration: float) -> str:
    pen = int(round(float(penetration) * 100))
    return f"seed{seed}_{volume}_pen{pen}"


def write_csv(path: str | Path, rows: Iterable[dict], fieldnames: list[str]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_csv(path: str | Path) -> list[dict]:
    with Path(path).open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_json(path: str | Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def weighted_choice(rng: random.Random, weights: dict[str, float]) -> str:
    total = sum(max(0.0, float(v)) for v in weights.values())
    if total <= 0:
        raise ValueError("Weights must sum to a positive value")
    pick = rng.random() * total
    acc = 0.0
    for key, weight in weights.items():
        acc += max(0.0, float(weight))
        if pick <= acc:
            return key
    return next(reversed(weights))


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(float(x1) - float(x2), float(y1) - float(y2))


APPROACHES = {
    "N": {"in": "N_in", "out": "N_out"},
    "E": {"in": "E_in", "out": "E_out"},
    "S": {"in": "S_in", "out": "S_out"},
    "W": {"in": "W_in", "out": "W_out"}
}

OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}
LEFT = {"N": "E", "E": "S", "S": "W", "W": "N"}
RIGHT = {"N": "W", "W": "S", "S": "E", "E": "N"}


def movement_to_destination(origin: str, movement: str) -> str:
    if movement == "through":
        return OPPOSITE[origin]
    if movement == "left":
        return LEFT[origin]
    if movement == "right":
        return RIGHT[origin]
    raise ValueError(f"Unknown movement: {movement}")

