# T-Junction Geometry Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a route-level T-junction geometry layer that exports reference paths, movement conflicts, and route-zone occupancies for prediction, labels, safety metrics, and coalition allocation.

**Architecture:** Keep the formal geometry independent from SUMO internals: `topology.py` defines legal movements, the new `route_geometry.py` derives lane-offset reference paths and conflict zones from scenario config, and existing log/label/metric modules consume the generated geometry artifact. The current center-circle flow remains available as debug fallback, but the T-junction paper path uses route-level zones.

**Tech Stack:** Python standard library, SUMO/TraCI already used by the prototype, XML/CSV/JSON artifacts, `unittest`; no new geometry dependency in this implementation pass.

---

## File Structure

- Create `sim/prototype/src/route_geometry.py`: lane-center geometry, sampled route paths, static conflict matrix, conflict-zone artifact export.
- Create `sim/prototype/tests/test_route_geometry.py`: unit tests for lane offsets, six T-junction routes, conflict matrix invariants, and zone distances.
- Modify `sim/prototype/config/t_junction_scenario.json`: add explicit geometry parameters from the spec.
- Modify `sim/prototype/src/common.py`: add `geometry_artifact_path(cfg)` helper and include the generated geometry directory if needed.
- Modify `sim/prototype/src/generate_network.py`: pass lane width into SUMO edge generation and write the geometry artifact after network generation.
- Modify `sim/prototype/src/render_network_preview.py`: render the route-level conflict zones when the artifact exists.
- Modify `sim/prototype/src/extract_conflict_events.py`: support `route_zones` mode that emits one event per vehicle-route-zone occupancy.
- Modify `sim/prototype/src/generate_yield_labels.py`: pair vehicles by route-level zone and conflict type instead of only center circle.
- Modify `sim/prototype/src/safety_metrics.py`: compute PET/entry-gap metrics from route-level zones while retaining center-circle helpers.
- Modify `sim/prototype/src/build_graph_prediction_dataset.py`: choose neighbors by shared route-level conflict zones instead of only distance-to-center.
- Modify `sim/prototype/tests/test_t_junction_geometry.py`: keep existing network/route tests and add artifact-generation checks.
- Modify `sim/prototype/tests/test_safety_metrics.py`: add route-zone occupancy and non-conflicting through-pair tests.
- Modify `sim/prototype/tests/test_priority_predictor.py` only if the graph dataset schema adds required edge fields.

---

### Task 1: Config Contract And Geometry Parameters

**Files:**
- Modify: `sim/prototype/config/t_junction_scenario.json`
- Modify: `sim/prototype/src/common.py`
- Modify: `sim/prototype/tests/test_t_junction_geometry.py`

- [ ] **Step 1: Write the failing config-contract test**

Add this test to `sim/prototype/tests/test_t_junction_geometry.py`:

```python
def test_t_junction_config_exposes_geometry_layer_parameters(self) -> None:
    cfg = json.loads((PROTOTYPE_ROOT / "config" / "t_junction_scenario.json").read_text(encoding="utf-8"))

    self.assertEqual(cfg["intersection_type"], "t_junction")
    self.assertEqual(cfg["active_approaches"], ["N", "E", "S"])
    self.assertEqual(cfg["lane_width_m"], 3.5)
    self.assertEqual(cfg["turn_radius_m"], 10.0)
    self.assertEqual(cfg["vehicle_dimensions_m"], {"length": 4.5, "width": 1.8})
    self.assertEqual(cfg["geometry_safety_buffer_m"], 0.5)
    self.assertEqual(cfg["control_region_distance_m"], 45.0)
    self.assertEqual(cfg["path_sample_interval_m"], 0.25)
    self.assertEqual(cfg["static_overlap_tolerance_m2"], 0.25)
    self.assertEqual(cfg["geometry_mode"], "route_zones")
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
python -m unittest sim.prototype.tests.test_t_junction_geometry.TJunctionGeometryTest.test_t_junction_config_exposes_geometry_layer_parameters
```

Expected: FAIL because the new geometry keys are missing.

- [ ] **Step 3: Add the geometry parameters to the scenario config**

Update `sim/prototype/config/t_junction_scenario.json` so the top-level object includes:

```json
{
  "lane_width_m": 3.5,
  "turn_radius_m": 10.0,
  "vehicle_dimensions_m": {
    "length": 4.5,
    "width": 1.8
  },
  "geometry_safety_buffer_m": 0.5,
  "control_region_distance_m": 45.0,
  "path_sample_interval_m": 0.25,
  "static_overlap_tolerance_m2": 0.25,
  "geometry_mode": "route_zones"
}
```

Keep the existing center-circle `conflict_zones` entry for debug compatibility.

- [ ] **Step 4: Add a geometry artifact path helper**

Add this helper to `sim/prototype/src/common.py`:

```python
def geometry_artifact_path(cfg: dict) -> Path:
    scenario = _slug(str(cfg.get("scenario_name") or cfg.get("intersection_type", "scenario")))
    return PROTOTYPE_ROOT / "networks" / f"{scenario}_route_geometry.json"
```

- [ ] **Step 5: Run the config-contract test**

Run:

```powershell
python -m unittest sim.prototype.tests.test_t_junction_geometry.TJunctionGeometryTest.test_t_junction_config_exposes_geometry_layer_parameters
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```powershell
git add sim/prototype/config/t_junction_scenario.json sim/prototype/src/common.py sim/prototype/tests/test_t_junction_geometry.py
git commit -m "feat: add t junction geometry config contract"
```

---

### Task 2: Route Geometry Module

**Files:**
- Create: `sim/prototype/src/route_geometry.py`
- Create: `sim/prototype/tests/test_route_geometry.py`

- [ ] **Step 1: Write failing tests for route paths and lane offsets**

Create `sim/prototype/tests/test_route_geometry.py` with:

```python
from __future__ import annotations

import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from route_geometry import build_route_geometry  # noqa: E402


def cfg() -> dict:
    return {
        "intersection_type": "t_junction",
        "active_approaches": ["N", "E", "S"],
        "approach_length_m": 120.0,
        "lane_width_m": 3.5,
        "turn_radius_m": 10.0,
        "vehicle_dimensions_m": {"length": 4.5, "width": 1.8},
        "geometry_safety_buffer_m": 0.5,
        "path_sample_interval_m": 0.25,
        "static_overlap_tolerance_m2": 0.25,
    }


class RouteGeometryTest(unittest.TestCase):
    def test_builds_six_t_junction_route_paths(self) -> None:
        artifact = build_route_geometry(cfg())

        self.assertEqual(
            set(artifact["routes"]),
            {"r_N_through", "r_N_left", "r_S_through", "r_S_right", "r_E_right", "r_E_left"},
        )
        self.assertNotIn("r_E_through", artifact["routes"])
        self.assertNotIn("r_W_left", artifact["routes"])

    def test_lane_offset_keeps_major_through_routes_apart(self) -> None:
        artifact = build_route_geometry(cfg())
        n_points = artifact["routes"]["r_N_through"]["points"]
        s_points = artifact["routes"]["r_S_through"]["points"]

        self.assertAlmostEqual(n_points[0]["x"], -1.75, places=2)
        self.assertAlmostEqual(s_points[0]["x"], 1.75, places=2)
        self.assertFalse(artifact["conflict_matrix"]["r_N_through"]["r_S_through"]["conflicts"])

    def test_route_pair_conflict_types_include_merging_and_crossing(self) -> None:
        artifact = build_route_geometry(cfg())

        self.assertEqual(
            artifact["conflict_matrix"]["r_N_left"]["r_S_right"]["conflict_type"],
            "merging",
        )
        self.assertIn(
            artifact["conflict_matrix"]["r_N_through"]["r_E_left"]["conflict_type"],
            {"crossing", "overlap_turning"},
        )

    def test_every_conflicting_pair_has_zone_with_entry_distances(self) -> None:
        artifact = build_route_geometry(cfg())
        zones = artifact["zones"]

        self.assertGreater(len(zones), 0)
        for zone in zones:
            self.assertGreater(zone["radius_m"], 0.0)
            for route_id in zone["route_ids"]:
                self.assertIn(route_id, zone["entry_distance_by_route"])
                self.assertIn(route_id, zone["exit_distance_by_route"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```powershell
python -m unittest sim.prototype.tests.test_route_geometry
```

Expected: FAIL because `route_geometry.py` does not exist.

- [ ] **Step 3: Create the route geometry module**

Create `sim/prototype/src/route_geometry.py` with these public functions and data fields:

```python
from __future__ import annotations

import json
import math
from pathlib import Path

from common import geometry_artifact_path, write_json
from topology import active_approaches, route_specs


LANE_SIGN = {
    "N": {"in": -1.0, "out": 1.0},
    "S": {"in": 1.0, "out": -1.0},
    "E": {"in": 1.0, "out": -1.0},
    "W": {"in": -1.0, "out": 1.0},
}


def _unit(approach: str, inbound: bool) -> tuple[float, float]:
    vectors = {
        ("N", True): (0.0, -1.0),
        ("N", False): (0.0, 1.0),
        ("S", True): (0.0, 1.0),
        ("S", False): (0.0, -1.0),
        ("E", True): (-1.0, 0.0),
        ("E", False): (1.0, 0.0),
        ("W", True): (1.0, 0.0),
        ("W", False): (-1.0, 0.0),
    }
    return vectors[(approach, inbound)]


def _lane_point(approach: str, inbound: bool, length: float, lane_width: float) -> tuple[float, float]:
    offset = lane_width / 2.0
    if approach == "N":
        return (LANE_SIGN["N"]["in" if inbound else "out"] * offset, length)
    if approach == "S":
        return (LANE_SIGN["S"]["in" if inbound else "out"] * offset, -length)
    if approach == "E":
        return (length, LANE_SIGN["E"]["in" if inbound else "out"] * offset)
    if approach == "W":
        return (-length, LANE_SIGN["W"]["in" if inbound else "out"] * offset)
    raise ValueError(f"Unknown approach: {approach}")


def _line_sample(start: tuple[float, float], end: tuple[float, float], ds: float) -> list[tuple[float, float]]:
    length = math.dist(start, end)
    count = max(1, int(math.ceil(length / ds)))
    return [
        (start[0] + (end[0] - start[0]) * i / count, start[1] + (end[1] - start[1]) * i / count)
        for i in range(count + 1)
    ]


def _normal_left(vector: tuple[float, float]) -> tuple[float, float]:
    return (-vector[1], vector[0])


def _normal_right(vector: tuple[float, float]) -> tuple[float, float]:
    return (vector[1], -vector[0])


def _arc_sample(
    center: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
    clockwise: bool,
    ds: float,
) -> list[tuple[float, float]]:
    radius = math.dist(center, start)
    a0 = math.atan2(start[1] - center[1], start[0] - center[0])
    a1 = math.atan2(end[1] - center[1], end[0] - center[0])
    if clockwise and a1 > a0:
        a1 -= 2.0 * math.pi
    if not clockwise and a1 < a0:
        a1 += 2.0 * math.pi
    arc_len = abs(a1 - a0) * radius
    count = max(2, int(math.ceil(arc_len / ds)))
    return [
        (center[0] + radius * math.cos(a0 + (a1 - a0) * i / count),
         center[1] + radius * math.sin(a0 + (a1 - a0) * i / count))
        for i in range(count + 1)
    ]
```

Then add these implementation pieces in the same file:

```python
def _route_path(origin: str, destination: str, length: float, lane_width: float, turn_radius: float, ds: float) -> list[tuple[float, float]]:
    start = _lane_point(origin, inbound=True, length=length, lane_width=lane_width)
    end = _lane_point(destination, inbound=False, length=length, lane_width=lane_width)
    in_dir = _unit(origin, inbound=True)
    out_dir = _unit(destination, inbound=False)
    cross = in_dir[0] * out_dir[1] - in_dir[1] * out_dir[0]
    if abs(cross) < 1e-9:
        return _line_sample(start, end, ds)

    if origin in {"N", "S"}:
        ix = start[0]
    else:
        ix = end[0]
    if origin in {"E", "W"}:
        iy = start[1]
    else:
        iy = end[1]
    intersection = (ix, iy)
    entry = (intersection[0] - in_dir[0] * turn_radius, intersection[1] - in_dir[1] * turn_radius)
    exit_point = (intersection[0] + out_dir[0] * turn_radius, intersection[1] + out_dir[1] * turn_radius)
    normal = _normal_left(in_dir) if cross > 0.0 else _normal_right(in_dir)
    center = (entry[0] + normal[0] * turn_radius, entry[1] + normal[1] * turn_radius)
    clockwise = cross < 0.0
    return (
        _line_sample(start, entry, ds)[:-1]
        + _arc_sample(center, entry, exit_point, clockwise=clockwise, ds=ds)[:-1]
        + _line_sample(exit_point, end, ds)
    )


def _with_distance(points: list[tuple[float, float]]) -> list[dict]:
    out = []
    total = 0.0
    previous = None
    for x, y in points:
        if previous is not None:
            total += math.dist(previous, (x, y))
        out.append({"x": round(x, 4), "y": round(y, 4), "s": round(total, 4)})
        previous = (x, y)
    return out


def _min_distance_pair(points_a: list[dict], points_b: list[dict]) -> tuple[float, dict, dict]:
    best = (float("inf"), points_a[0], points_b[0])
    for pa in points_a:
        for pb in points_b:
            dist = math.hypot(pa["x"] - pb["x"], pa["y"] - pb["y"])
            if dist < best[0]:
                best = (dist, pa, pb)
    return best


def _classify(route_a: dict, route_b: dict, min_dist: float, threshold: float) -> str:
    if route_a["origin"] == route_b["origin"]:
        return "diverging"
    if route_a["destination"] == route_b["destination"]:
        return "merging"
    if min_dist <= threshold:
        return "crossing"
    return "none"


def build_route_geometry(cfg: dict) -> dict:
    length = float(cfg["approach_length_m"])
    lane_width = float(cfg.get("lane_width_m", 3.5))
    turn_radius = float(cfg.get("turn_radius_m", 10.0))
    ds = float(cfg.get("path_sample_interval_m", 0.25))
    vehicle_width = float(cfg.get("vehicle_dimensions_m", {}).get("width", 1.8))
    safety_buffer = float(cfg.get("geometry_safety_buffer_m", 0.5))
    buffer_radius = vehicle_width / 2.0 + safety_buffer
    conflict_distance = 2.0 * buffer_radius

    routes = {}
    for spec in route_specs(active_approaches(cfg)):
        points = _with_distance(_route_path(spec.origin, spec.destination, length, lane_width, turn_radius, ds))
        routes[spec.route_id] = {
            "route_id": spec.route_id,
            "origin": spec.origin,
            "destination": spec.destination,
            "movement": spec.movement,
            "points": points,
        }

    matrix = {route_id: {} for route_id in routes}
    zones = []
    zone_index = 0
    route_items = list(routes.items())
    for route_a, data_a in route_items:
        for route_b, data_b in route_items:
            if route_a == route_b:
                matrix[route_a][route_b] = {"conflicts": True, "conflict_type": "queue_following", "zone_ids": []}
                continue
            min_dist, pa, pb = _min_distance_pair(data_a["points"], data_b["points"])
            conflict_type = _classify(data_a, data_b, min_dist, conflict_distance)
            conflicts = conflict_type != "none"
            zone_ids = []
            if conflicts and route_a < route_b:
                zone_index += 1
                zone_id = f"z_{zone_index:03d}"
                centroid = {"x": round((pa["x"] + pb["x"]) / 2.0, 4), "y": round((pa["y"] + pb["y"]) / 2.0, 4)}
                zones.append({
                    "zone_id": zone_id,
                    "route_ids": [route_a, route_b],
                    "conflict_type": conflict_type,
                    "centroid": centroid,
                    "radius_m": round(max(buffer_radius, min_dist / 2.0 + buffer_radius), 4),
                    "entry_distance_by_route": {
                        route_a: round(max(0.0, pa["s"] - buffer_radius), 4),
                        route_b: round(max(0.0, pb["s"] - buffer_radius), 4),
                    },
                    "exit_distance_by_route": {
                        route_a: round(pa["s"] + buffer_radius, 4),
                        route_b: round(pb["s"] + buffer_radius, 4),
                    },
                })
                zone_ids = [zone_id]
            matrix[route_a][route_b] = {"conflicts": conflicts, "conflict_type": conflict_type, "zone_ids": zone_ids}

    zone_by_pair = {}
    for zone in zones:
        a, b = zone["route_ids"]
        zone_by_pair[(a, b)] = zone["zone_id"]
        zone_by_pair[(b, a)] = zone["zone_id"]
    for route_a in matrix:
        for route_b in matrix[route_a]:
            if route_a != route_b and matrix[route_a][route_b]["conflicts"]:
                matrix[route_a][route_b]["zone_ids"] = [zone_by_pair[(route_a, route_b)]]

    return {
        "intersection_type": str(cfg.get("intersection_type", "t_junction")),
        "active_approaches": list(active_approaches(cfg)),
        "parameters": {
            "approach_length_m": length,
            "lane_width_m": lane_width,
            "turn_radius_m": turn_radius,
            "vehicle_width_m": vehicle_width,
            "geometry_safety_buffer_m": safety_buffer,
            "buffer_radius_m": buffer_radius,
            "path_sample_interval_m": ds,
        },
        "routes": routes,
        "conflict_matrix": matrix,
        "zones": zones,
    }


def write_route_geometry(cfg: dict, path: str | Path | None = None) -> Path:
    artifact = build_route_geometry(cfg)
    out_path = Path(path) if path is not None else geometry_artifact_path(cfg)
    write_json(out_path, artifact)
    return out_path


def load_route_geometry(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)
```

- [ ] **Step 4: Run the route geometry tests**

Run:

```powershell
python -m unittest sim.prototype.tests.test_route_geometry
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add sim/prototype/src/route_geometry.py sim/prototype/tests/test_route_geometry.py
git commit -m "feat: add route-level t junction geometry"
```

---

### Task 3: Geometry Artifact Export And Network Integration

**Files:**
- Modify: `sim/prototype/src/generate_network.py`
- Modify: `sim/prototype/src/render_network_preview.py`
- Modify: `sim/prototype/tests/test_t_junction_geometry.py`

- [ ] **Step 1: Write a failing artifact-generation test**

Add this test to `sim/prototype/tests/test_t_junction_geometry.py`:

```python
def test_generate_network_writes_route_geometry_artifact(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "t_config.json"
        _write_t_config(config_path)
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        payload.update({
            "lane_width_m": 3.5,
            "turn_radius_m": 10.0,
            "vehicle_dimensions_m": {"length": 4.5, "width": 1.8},
            "geometry_safety_buffer_m": 0.5,
            "path_sample_interval_m": 0.25,
            "static_overlap_tolerance_m2": 0.25,
            "geometry_mode": "route_zones",
        })
        config_path.write_text(json.dumps(payload), encoding="utf-8")

        with patch("generate_network.subprocess.run"):
            outputs = generate_network(str(config_path))

        self.assertIn("geometry", outputs)
        artifact = json.loads(outputs["geometry"].read_text(encoding="utf-8"))
        self.assertEqual(set(artifact["active_approaches"]), {"N", "E", "S"})
        self.assertIn("r_N_through", artifact["routes"])
        self.assertGreater(len(artifact["zones"]), 0)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
python -m unittest sim.prototype.tests.test_t_junction_geometry.TJunctionGeometryTest.test_generate_network_writes_route_geometry_artifact
```

Expected: FAIL because `generate_network` does not return or write the geometry artifact.

- [ ] **Step 3: Export geometry from network generation**

Modify `sim/prototype/src/generate_network.py`:

```python
from route_geometry import write_route_geometry
```

Inside `generate_network`, after writing the node/edge/connection XML and before returning:

```python
    geometry = write_route_geometry(cfg)
```

Set lane width on generated SUMO edges:

```python
    lane_width = float(cfg.get("lane_width_m", 3.5))
```

and include it in each edge:

```python
            width=f"{lane_width:.2f}",
```

Return the artifact:

```python
    return {"nodes": nod, "edges": edg, "connections": con, "network": net, "geometry": geometry}
```

- [ ] **Step 4: Keep preview compatible and add route-zone overlay**

Modify `sim/prototype/src/render_network_preview.py` so `render_preview` attempts to read the geometry artifact and draws circles for generated zones:

```python
from common import geometry_artifact_path
```

Inside `render_preview`, after `c = p("C")`:

```python
    zone_overlay_svg = ""
    artifact_path = geometry_artifact_path(cfg)
    if artifact_path.exists():
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        zone_items = []
        for zone in artifact.get("zones", []):
            zx, zy = _scale((zone["centroid"]["x"], zone["centroid"]["y"]), center_origin, canvas, margin, length)
            zr = float(zone["radius_m"]) * (canvas / 2 - margin) / length
            zone_items.append(
                f'<circle cx="{zx:.1f}" cy="{zy:.1f}" r="{zr:.1f}" fill="#fef9c3" stroke="#ca8a04" stroke-width="1.5" opacity="0.65" />'
            )
        zone_overlay_svg = "\n  ".join(zone_items)
```

Insert `{zone_overlay_svg}` before the debug center circle in the SVG string.

- [ ] **Step 5: Run focused tests**

Run:

```powershell
python -m unittest sim.prototype.tests.test_t_junction_geometry sim.prototype.tests.test_route_geometry
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```powershell
git add sim/prototype/src/generate_network.py sim/prototype/src/render_network_preview.py sim/prototype/tests/test_t_junction_geometry.py
git commit -m "feat: export t junction geometry artifact"
```

---

### Task 4: Route-Zone Event Extraction And Labels

**Files:**
- Modify: `sim/prototype/src/extract_conflict_events.py`
- Modify: `sim/prototype/src/generate_yield_labels.py`
- Create: `sim/prototype/tests/test_route_zone_events.py`

- [ ] **Step 1: Write failing tests for route-zone occupancies**

Create `sim/prototype/tests/test_route_zone_events.py` with:

```python
from __future__ import annotations

import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from extract_conflict_events import extract_route_zone_events_from_rows  # noqa: E402
from route_geometry import build_route_geometry  # noqa: E402


def cfg() -> dict:
    return {
        "intersection_type": "t_junction",
        "active_approaches": ["N", "E", "S"],
        "approach_length_m": 120.0,
        "lane_width_m": 3.5,
        "turn_radius_m": 10.0,
        "vehicle_dimensions_m": {"length": 4.5, "width": 1.8},
        "geometry_safety_buffer_m": 0.5,
        "path_sample_interval_m": 0.5,
        "static_overlap_tolerance_m2": 0.25,
        "label_thresholds": {"pre_zone_window_s": 3.0},
    }


def state(time: float, veh_id: str, route_id: str, x: float, y: float, accel: float = 0.0) -> dict:
    origin = route_id.split("_")[1]
    movement = route_id.split("_")[2]
    return {
        "time": f"{time:.1f}",
        "veh_id": veh_id,
        "veh_class": "HDV" if veh_id.startswith("h") else "CAV",
        "veh_type": "HDV" if veh_id.startswith("h") else "CAV",
        "route_id": route_id,
        "origin": origin,
        "destination": "",
        "movement": movement,
        "x": f"{x:.3f}",
        "y": f"{y:.3f}",
        "acceleration": f"{accel:.3f}",
        "speed": "5.000",
    }


class RouteZoneEventsTest(unittest.TestCase):
    def test_extracts_events_only_for_zones_on_vehicle_route(self) -> None:
        artifact = build_route_geometry(cfg())
        zone = next(z for z in artifact["zones"] if "r_N_through" in z["route_ids"] and "r_E_left" in z["route_ids"])
        cx = zone["centroid"]["x"]
        cy = zone["centroid"]["y"]
        rows = [
            state(0.0, "h1", "r_N_through", cx, cy + 6.0),
            state(1.0, "h1", "r_N_through", cx, cy),
            state(2.0, "h1", "r_N_through", cx, cy + 6.0),
            state(1.0, "c1", "r_S_through", cx, cy),
        ]

        events = extract_route_zone_events_from_rows(rows, artifact, pre_zone_window_s=3.0)

        self.assertEqual([event["veh_id"] for event in events], ["h1"])
        self.assertEqual(events[0]["zone_id"], zone["zone_id"])
        self.assertIn("conflict_type", events[0])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
python -m unittest sim.prototype.tests.test_route_zone_events
```

Expected: FAIL because `extract_route_zone_events_from_rows` does not exist.

- [ ] **Step 3: Add route-zone extraction helpers**

Modify `sim/prototype/src/extract_conflict_events.py`:

```python
from common import geometry_artifact_path
from route_geometry import load_route_geometry
```

Add:

```python
def _distance_xy(row: dict, centroid: dict) -> float:
    return ((float(row["x"]) - float(centroid["x"])) ** 2 + (float(row["y"]) - float(centroid["y"])) ** 2) ** 0.5


def extract_route_zone_events_from_rows(rows: list[dict], artifact: dict, pre_zone_window_s: float) -> list[dict]:
    route_zones = {}
    zone_by_id = {}
    for zone in artifact.get("zones", []):
        zone_by_id[zone["zone_id"]] = zone
        for route_id in zone.get("route_ids", []):
            route_zones.setdefault(route_id, []).append(zone)

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
                if _distance_xy(r, zone["centroid"]) <= float(zone["radius_m"])
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
                "conflict_type": zone["conflict_type"],
                "zone_route_ids": "|".join(zone["route_ids"]),
                "entry_time": entry["time"],
                "exit_time": exit_row["time"],
                "min_pre_zone_accel": f"{min_accel:.3f}",
                "min_pre_zone_speed": f"{min_speed:.3f}",
            })
    events.sort(key=lambda item: (float(item["entry_time"]), item["veh_id"], item["zone_id"]))
    return events
```

Update `extract_events` so when `cfg.get("geometry_mode") == "route_zones"` it loads `geometry_artifact_path(cfg)` and calls `extract_route_zone_events_from_rows`. Keep the existing center-circle branch as the fallback.

- [ ] **Step 4: Update event CSV fields**

In `extract_conflict_events.py`, extend the event fields to:

```python
fields = [
    "veh_id", "veh_class", "veh_type", "route_id", "origin", "destination", "movement",
    "zone_id", "conflict_type", "zone_route_ids",
    "entry_time", "exit_time", "min_pre_zone_accel", "min_pre_zone_speed",
]
```

For center-circle fallback rows, set:

```python
"conflict_type": "center_debug",
"zone_route_ids": "",
```

- [ ] **Step 5: Update label pairing by route-level zone**

Modify `sim/prototype/src/generate_yield_labels.py` so event pairs are skipped when the pair is not a priority-style route conflict:

```python
PRIORITY_LABEL_CONFLICT_TYPES = {"crossing", "merging", "overlap_turning"}
```

Inside the pair loop:

```python
        if a.get("conflict_type") and a.get("conflict_type") not in PRIORITY_LABEL_CONFLICT_TYPES:
            continue
        route_ids = set(str(a.get("zone_route_ids", "")).split("|"))
        if a.get("route_id") not in route_ids or b.get("route_id") not in route_ids:
            continue
```

Remove the unconditional same-origin skip for route-zone mode; route-zone type filtering now decides whether the pair supports a priority label.

- [ ] **Step 6: Run route-zone event tests**

Run:

```powershell
python -m unittest sim.prototype.tests.test_route_zone_events sim.prototype.tests.test_t_junction_geometry
```

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```powershell
git add sim/prototype/src/extract_conflict_events.py sim/prototype/src/generate_yield_labels.py sim/prototype/tests/test_route_zone_events.py
git commit -m "feat: extract route-level conflict events"
```

---

### Task 5: Route-Zone Safety Metrics And Graph Neighbors

**Files:**
- Modify: `sim/prototype/src/safety_metrics.py`
- Modify: `sim/prototype/src/build_graph_prediction_dataset.py`
- Modify: `sim/prototype/tests/test_safety_metrics.py`

- [ ] **Step 1: Write failing route-zone safety tests**

Add this test to `sim/prototype/tests/test_safety_metrics.py`:

```python
def test_route_zone_metrics_do_not_count_compatible_major_through_pair(self) -> None:
    events = [
        {
            "veh_id": "a",
            "veh_class": "CAV",
            "origin": "N",
            "destination": "S",
            "movement": "through",
            "route_id": "r_N_through",
            "zone_id": "z_major",
            "conflict_type": "none",
            "entry_time": "1.0",
            "exit_time": "2.0",
        },
        {
            "veh_id": "b",
            "veh_class": "CAV",
            "origin": "S",
            "destination": "N",
            "movement": "through",
            "route_id": "r_S_through",
            "zone_id": "z_major",
            "conflict_type": "none",
            "entry_time": "1.2",
            "exit_time": "2.2",
        },
    ]

    metrics = compute_route_zone_safety_metrics(events, near_conflict_pet_s=1.5)

    self.assertEqual(metrics["conflict_pair_count"], 0)
    self.assertEqual(metrics["near_conflict_count"], 0)
```

Import the new function:

```python
from safety_metrics import compute_route_zone_safety_metrics
```

- [ ] **Step 2: Run the safety test to verify it fails**

Run:

```powershell
python -m unittest sim.prototype.tests.test_safety_metrics.SafetyMetricsTest.test_route_zone_metrics_do_not_count_compatible_major_through_pair
```

Expected: FAIL because `compute_route_zone_safety_metrics` does not exist.

- [ ] **Step 3: Add route-zone safety metrics**

Add this to `sim/prototype/src/safety_metrics.py`:

```python
ROUTE_ZONE_CONFLICT_TYPES = {"crossing", "merging", "overlap_turning", "queue_following"}


def compute_route_zone_safety_metrics(events: list[dict], near_conflict_pet_s: float) -> dict:
    pets = []
    entry_gaps = []
    for a, b in combinations(events, 2):
        if a["veh_id"] == b["veh_id"]:
            continue
        if a["zone_id"] != b["zone_id"]:
            continue
        conflict_type = a.get("conflict_type") or b.get("conflict_type", "")
        if conflict_type not in ROUTE_ZONE_CONFLICT_TYPES:
            continue
        entry_a = float(a["entry_time"])
        exit_a = float(a["exit_time"])
        entry_b = float(b["entry_time"])
        exit_b = float(b["exit_time"])
        first_exit, second_entry = (exit_a, entry_b) if entry_a <= entry_b else (exit_b, entry_a)
        pets.append(second_entry - first_exit)
        entry_gaps.append(abs(entry_a - entry_b))
    near_conflicts = [pet for pet in pets if pet <= near_conflict_pet_s]
    return {
        "occupancy_count": len(events),
        "conflict_pair_count": len(pets),
        "near_conflict_count": len(near_conflicts),
        "near_conflict_pet_threshold_s": near_conflict_pet_s,
        "min_pet_s": min(pets) if pets else None,
        "mean_pet_s": sum(pets) / len(pets) if pets else None,
        "min_entry_gap_s": min(entry_gaps) if entry_gaps else None,
    }
```

Update `write_safety_outputs` to accept optional `events_csv` and `geometry_mode` arguments. When `geometry_mode == "route_zones"` and `events_csv` exists, compute metrics from route-zone events; otherwise use the existing center-circle flow.

- [ ] **Step 4: Update graph neighbor selection**

In `sim/prototype/src/build_graph_prediction_dataset.py`, add a helper:

```python
def _shared_conflict_zone(route_a: str, route_b: str, artifact: dict) -> str:
    if not route_a or not route_b or route_a == route_b:
        return ""
    relation = artifact.get("conflict_matrix", {}).get(route_a, {}).get(route_b, {})
    if not relation.get("conflicts"):
        return ""
    zone_ids = relation.get("zone_ids", [])
    return zone_ids[0] if zone_ids else ""
```

Modify `_candidate_neighbors` so when an artifact is supplied it filters candidates by `_shared_conflict_zone(target_route, neighbor_route, artifact)` and includes:

```python
edge["shared_route_zone_id"] = zone_id
edge["route_conflict_type"] = artifact["conflict_matrix"][target_route][neighbor_route]["conflict_type"]
```

Keep the distance-based filter as fallback when no artifact is available.

- [ ] **Step 5: Run safety and dataset tests**

Run:

```powershell
python -m unittest sim.prototype.tests.test_safety_metrics sim.prototype.tests.test_priority_predictor
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```powershell
git add sim/prototype/src/safety_metrics.py sim/prototype/src/build_graph_prediction_dataset.py sim/prototype/tests/test_safety_metrics.py
git commit -m "feat: use route zones in safety and graph features"
```

---

### Task 6: Closed-Loop Integration And Verification

**Files:**
- Modify: `sim/prototype/src/run_closed_loop_allocation.py`
- Modify: `sim/prototype/src/run_sumo.py`
- Modify: `docs/experiments/prototype_validation_report_20260617.md`

- [ ] **Step 1: Update run metadata with geometry artifact**

In `sim/prototype/src/run_sumo.py`, import:

```python
from common import geometry_artifact_path
```

After `generate_network(config_path)`, set:

```python
    geometry_path = geometry_artifact_path(cfg)
```

Add to `run_meta`:

```python
"geometry_mode": cfg.get("geometry_mode", "center_debug"),
"geometry_artifact": str(geometry_path) if geometry_path.exists() else "",
```

- [ ] **Step 2: Feed route-zone events to closed-loop safety metrics**

In `sim/prototype/src/run_closed_loop_allocation.py`, import:

```python
from extract_conflict_events import extract_events
```

Before `write_safety_outputs`, call:

```python
    event_outputs = extract_events(config_path, output_name)
```

Then call `write_safety_outputs` with:

```python
        events_csv=event_outputs["events"],
        geometry_mode=str(cfg.get("geometry_mode", "center_debug")),
```

Add to the summary:

```python
"geometry_mode": cfg.get("geometry_mode", "center_debug"),
"conflict_events": event_outputs["events"],
```

- [ ] **Step 3: Run all local unit tests**

Run:

```powershell
python -m unittest sim.prototype.tests.test_route_geometry sim.prototype.tests.test_route_zone_events sim.prototype.tests.test_t_junction_geometry sim.prototype.tests.test_safety_metrics sim.prototype.tests.test_priority_predictor sim.prototype.tests.test_allocation_policy
```

Expected: PASS.

- [ ] **Step 4: Run a T-junction route-zone smoke test in the SUMO environment**

Run in the project root on the machine where SUMO is available:

```powershell
python sim/prototype/src/run_sumo.py --config sim/prototype/config/t_junction_scenario.json --seed 1 --volume low --penetration 0.5 --duration 60
python sim/prototype/src/extract_conflict_events.py --config sim/prototype/config/t_junction_scenario.json --run-id t_junction_unsignalized_stress_p0_seed1_low_pen50
python sim/prototype/src/generate_yield_labels.py --config sim/prototype/config/t_junction_scenario.json --run-id t_junction_unsignalized_stress_p0_seed1_low_pen50
```

Expected:

```text
states: sim/prototype/logs/t_junction_unsignalized_stress_p0_seed1_low_pen50/vehicle_states.csv
events: sim/prototype/logs/t_junction_unsignalized_stress_p0_seed1_low_pen50/conflict_events.csv
label_count: greater than or equal to 1 for a non-empty smoke run
```

- [ ] **Step 5: Run a closed-loop smoke test**

Run:

```powershell
python sim/prototype/src/run_closed_loop_allocation.py --config sim/prototype/config/t_junction_scenario.json --seed 1 --volume low --penetration 0.5 --duration 60 --method fcfs
```

Expected:

```text
"geometry_mode": "route_zones"
"state_rows": greater than 0
"decision_rows": greater than 0
"conflict_pair_count": present in summary JSON
```

- [ ] **Step 6: Record verification results**

Append a short dated section to `docs/experiments/prototype_validation_report_20260617.md` by running:

```powershell
$rid = "t_junction_unsignalized_stress_p0_seed1_low_pen50"
$closedLoopSummary = Get-Content "sim/prototype/reports/${rid}_fcfs_closed_loop_summary.json" | ConvertFrom-Json
$eventsSummary = Get-Content "sim/prototype/reports/${rid}_events_summary.json" | ConvertFrom-Json
$labelSummary = Get-Content "sim/prototype/reports/${rid}_label_summary.json" | ConvertFrom-Json
$section = @"

## T-Junction Route-Zone Geometry Smoke Test

Date: 2026-06-17

Configuration: ``sim/prototype/config/t_junction_scenario.json``

Checks:

- Unit tests: passed for route geometry, route-zone events, T-junction topology, safety metrics, priority predictor, and allocation policy.
- SUMO smoke run: route-zone geometry artifact generated and used by event extraction.
- Closed-loop smoke run: summary contains ``geometry_mode=$($closedLoopSummary.geometry_mode)`` and route-level conflict metrics.

Observed counts:

- ``state_rows``: $($closedLoopSummary.state_rows)
- ``event_count``: $($eventsSummary.event_count)
- ``label_count``: $($labelSummary.label_count)
- ``conflict_pair_count``: $($closedLoopSummary.conflict_pair_count)
- ``near_conflict_count``: $($closedLoopSummary.near_conflict_count)
"@
Add-Content -Path "docs/experiments/prototype_validation_report_20260617.md" -Value $section
```

- [ ] **Step 7: Commit**

Run:

```powershell
git add sim/prototype/src/run_sumo.py sim/prototype/src/run_closed_loop_allocation.py docs/experiments/prototype_validation_report_20260617.md
git commit -m "feat: wire route-zone geometry into closed-loop runs"
```

---

## Self-Review

Spec coverage:

- Geometry parameters: Task 1.
- Six legal T-junction movements and no west-leg routes: Task 2 and existing topology tests.
- Lane-offset right-hand traffic convention: Task 2.
- Reference paths and sampled distances: Task 2.
- Swept-area approximation and static conflict matrix: Task 2.
- Conflict-zone artifact and per-route entry/exit distances: Task 2 and Task 3.
- SUMO network integration and lane width: Task 3.
- Route-zone event extraction and labels: Task 4.
- Route-level safety metrics and graph neighbors: Task 5.
- Closed-loop verification: Task 6.

Placeholder scan:

- No unresolved requirement markers are intentionally left in the plan.
- Smoke-run counts are recorded by a PowerShell snippet that reads the generated JSON summaries.

Type consistency:

- `geometry_artifact_path(cfg)` returns a `Path`.
- `build_route_geometry(cfg)` returns a JSON-serializable `dict`.
- `write_route_geometry(cfg, path=None)` returns a `Path`.
- `extract_route_zone_events_from_rows(rows, artifact, pre_zone_window_s)` returns `list[dict]`.
- `compute_route_zone_safety_metrics(events, near_conflict_pet_s)` returns the same metric keys as the existing center-circle safety path.
