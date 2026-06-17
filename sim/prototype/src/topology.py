from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from common import APPROACHES, movement_to_destination


DEFAULT_APPROACH_ORDER = ("N", "E", "S", "W")
T_JUNCTION_DEFAULT_APPROACHES = ("N", "E", "S")
MOVEMENTS = ("left", "through", "right")

NODE_COORDINATES = {
    "N": lambda length: (0.0, length),
    "E": lambda length: (length, 0.0),
    "S": lambda length: (0.0, -length),
    "W": lambda length: (-length, 0.0),
}


@dataclass(frozen=True)
class RouteSpec:
    origin: str
    movement: str
    destination: str

    @property
    def route_id(self) -> str:
        return f"r_{self.origin}_{self.movement}"

    @property
    def edges(self) -> str:
        return f"{APPROACHES[self.origin]['in']} {APPROACHES[self.destination]['out']}"


def active_approaches(cfg: dict) -> tuple[str, ...]:
    configured = cfg.get("active_approaches")
    if configured is None:
        intersection_type = str(cfg.get("intersection_type", "four_leg")).lower()
        configured = T_JUNCTION_DEFAULT_APPROACHES if intersection_type in {"t_junction", "t-junction", "t"} else DEFAULT_APPROACH_ORDER

    approaches = tuple(str(item).upper() for item in configured)
    if len(set(approaches)) != len(approaches):
        raise ValueError(f"Duplicate approaches are not allowed: {approaches}")
    unknown = [item for item in approaches if item not in APPROACHES]
    if unknown:
        raise ValueError(f"Unknown approach ids: {unknown}")
    if len(approaches) < 2:
        raise ValueError("At least two active approaches are required")
    return approaches


def node_specs(approaches: Iterable[str], length: float) -> list[tuple[str, float, float]]:
    specs = [("C", 0.0, 0.0)]
    for approach in approaches:
        x, y = NODE_COORDINATES[approach](length)
        specs.append((f"{approach}0", x, y))
    return specs


def edge_specs(approaches: Iterable[str]) -> list[tuple[str, str, str]]:
    specs = []
    for approach in approaches:
        node_id = f"{approach}0"
        specs.append((APPROACHES[approach]["in"], node_id, "C"))
        specs.append((APPROACHES[approach]["out"], "C", node_id))
    return specs


def connection_specs(approaches: Iterable[str]) -> list[tuple[str, str]]:
    active = tuple(approaches)
    specs = []
    for origin in active:
        for destination in active:
            if destination == origin:
                continue
            specs.append((APPROACHES[origin]["in"], APPROACHES[destination]["out"]))
    return specs


def route_specs(approaches: Iterable[str]) -> list[RouteSpec]:
    active = set(approaches)
    specs = []
    for origin in approaches:
        for movement in MOVEMENTS:
            destination = movement_to_destination(origin, movement)
            if destination in active and destination != origin:
                specs.append(RouteSpec(origin, movement, destination))
    return specs


def allowed_turn_weights(origin: str, approaches: Iterable[str], turn_weights: dict[str, float]) -> dict[str, float]:
    active = set(approaches)
    allowed = {}
    for movement in MOVEMENTS:
        destination = movement_to_destination(origin, movement)
        if destination in active and destination != origin:
            allowed[movement] = float(turn_weights.get(movement, 0.0))
    if sum(max(0.0, value) for value in allowed.values()) <= 0.0:
        allowed = {movement: 1.0 for movement in allowed}
    return allowed
