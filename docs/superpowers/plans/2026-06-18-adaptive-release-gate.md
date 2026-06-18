# Adaptive Release Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add and evaluate a geometry-aware adaptive release gate for the T-junction coalition allocator.

**Architecture:** Extend `VehicleState` with optional route metadata, then let `prediction_coalition` add one extra low-risk CAV beyond the base release set only when geometry and occupancy gates allow it. Propagate the new parameters through closed-loop, batch, and queue entry points so remote pilots are reproducible.

**Tech Stack:** Python standard library, `unittest`, SUMO/TraCI for remote simulation, existing prototype scripts under `sim/prototype`.

---

### Task 1: Policy-Level TDD

**Files:**

- Modify: `sim/prototype/tests/test_allocation_policy.py`
- Modify: `sim/prototype/src/allocation_policy.py`

- [ ] **Step 1: Write failing adaptive-gate unit tests**

Add tests for the following behaviors:

```python
def test_adaptive_gate_adds_low_risk_cav_on_non_conflicting_route(self) -> None:
    vehicles = [
        VehicleState("a", "CAV", 10.0, 5.0, 0.0, route_id="r_N_through"),
        VehicleState("b", "CAV", 18.0, 5.0, 0.0, route_id="r_S_through"),
        VehicleState("c", "CAV", 26.0, 5.0, 0.0, route_id="r_E_right"),
    ]
    route_conflicts = {
        "r_N_through": {"r_E_right": {"conflicts": False}, "r_S_through": {"conflicts": False}},
        "r_S_through": {"r_E_right": {"conflicts": False}, "r_N_through": {"conflicts": False}},
        "r_E_right": {"r_N_through": {"conflicts": False}, "r_S_through": {"conflicts": False}},
    }

    decision = build_decision(
        vehicles,
        method="prediction_coalition",
        max_release_count=2,
        safe_arrival_gap_s=1.0,
        adaptive_release_enabled=True,
        adaptive_max_release_count=3,
        route_conflict_matrix=route_conflicts,
        conflict_zone_occupancy=0,
    )

    self.assertEqual(decision.release_vehicles, ["a", "b", "c"])
```

Also add tests for conflicting route gap, occupancy blocking, HDV protection, and disabled default.

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
python -m unittest sim/prototype/tests/test_allocation_policy.py
```

Expected: fails because `VehicleState` and `build_decision` do not yet accept adaptive-gate fields.

- [ ] **Step 3: Implement minimal policy support**

Add optional route fields to `VehicleState`, add adaptive parameters to `build_decision`, and update `_select_release_set`.

- [ ] **Step 4: Run policy tests and verify GREEN**

Run:

```powershell
python -m unittest sim/prototype/tests/test_allocation_policy.py
```

Expected: all allocation policy tests pass.

### Task 2: Closed-Loop Parameter Propagation

**Files:**

- Modify: `sim/prototype/src/run_closed_loop_allocation.py`
- Modify: `sim/prototype/src/run_closed_loop_batch.py`
- Modify: `sim/prototype/src/run_formal_experiment_queue.py`
- Modify: `sim/prototype/tests/test_formal_experiment_queue.py`

- [ ] **Step 1: Add failing propagation tests**

Extend queue tests to assert adaptive defaults and manifest command flags:

```python
self.assertEqual(jobs[0].params["adaptive_release_enabled"], False)
self.assertIn("--adaptive-max-release-count", payload["jobs"][1]["command"])
```

- [ ] **Step 2: Run queue tests and verify RED**

Run:

```powershell
python -m unittest sim/prototype/tests/test_formal_experiment_queue.py
```

Expected: fails because adaptive parameters are missing.

- [ ] **Step 3: Implement propagation**

Add CLI arguments, summary fields, batch fields, and queue manifest flags.

- [ ] **Step 4: Enrich candidates with route metadata and occupancy**

Load geometry in closed loop, attach route metadata to `VehicleState`, compute conflict-zone occupancy, and pass both into `build_decision`.

- [ ] **Step 5: Run targeted tests**

Run:

```powershell
python -m unittest sim/prototype/tests/test_allocation_policy.py sim/prototype/tests/test_formal_experiment_queue.py
```

Expected: all targeted tests pass.

### Task 3: Verification and Commit

**Files:**

- Modify code and tests from Tasks 1-2.
- Commit only source/tests/docs, not generated reports.

- [ ] **Step 1: Run full local tests**

Run:

```powershell
python -m unittest discover sim/prototype/tests
```

Expected: all tests pass.

- [ ] **Step 2: Run diff check**

Run:

```powershell
git diff --check
```

Expected: no whitespace errors.

- [ ] **Step 3: Commit implementation**

Run:

```powershell
git add docs/superpowers/specs/2026-06-18-adaptive-release-gate-design.md docs/superpowers/plans/2026-06-18-adaptive-release-gate.md sim/prototype/src sim/prototype/tests
git commit -m "feat: add adaptive release gate"
```

### Task 4: Remote Pilot

**Files:**

- Remote deployment only.
- Later report: `docs/experiments/formal_pilot_adaptive_gate_300s_report_20260618.md`

- [ ] **Step 1: Deploy committed code to remote**

Use `git archive` locally and upload to an isolated remote directory under `/public/home/xiaohei_0/hx`.

- [ ] **Step 2: Run remote unit tests**

Run in remote `sumoenv`:

```bash
/public/home/xiaohei_0/conda38/bin/conda run -n sumoenv python -m unittest discover sim/prototype/tests
```

Expected: all tests pass.

- [ ] **Step 3: Start 300 s pilot**

Run remotely:

```bash
/public/home/xiaohei_0/conda38/bin/conda run -n sumoenv python sim/prototype/src/run_closed_loop_batch.py \
  --config sim/prototype/config/t_junction_scenario.json \
  --seeds 1,2,3 \
  --volumes medium,high \
  --penetrations 0.5,0.8 \
  --methods fcfs,prediction_coalition \
  --duration 300 \
  --max-release-count 2 \
  --adaptive-release-enabled \
  --adaptive-max-release-count 3 \
  --safe-arrival-gap-s 1.2 \
  --adaptive-min-conflict-arrival-gap-s 2.4 \
  --adaptive-max-occupancy 0 \
  --fairness-weight 0.0 \
  --cav-waiting-tiebreaker-weight 0.1 \
  --output-name formal_pilot_adaptive_gate_mr2_amr3_gap12_cgap24_occ0_fw0_tb01_seed1_3_mh_pen50_80_d300
```

- [ ] **Step 4: Copy back summary artifacts**

Copy back:

```text
closed_loop_batch_summary.json
closed_loop_batch_aggregate.csv
closed_loop_batch_runs.csv
```

- [ ] **Step 5: Write experiment report and update summary**

Compare adaptive gate against FCFS, S3, and W0. Do not claim final superiority unless the decision criteria are met.
