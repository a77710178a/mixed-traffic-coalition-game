# Formal Experiment Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reproducible formal-experiment queue for the T-junction route-zone paper experiments.

**Architecture:** Keep the existing batch runners as execution backends. Add a small queue module that builds named experiment jobs for E1, E2, A1, A2, and A3, supports dry-run manifests, optionally executes selected jobs, and records output paths without inventing result values.

**Tech Stack:** Python standard library, existing `run_label_sanity_batch.py`, existing `run_closed_loop_batch.py`, `unittest`.

---

### Task 1: Label Batch Output Names

**Files:**
- Modify: `sim/prototype/src/run_label_sanity_batch.py`
- Test: `sim/prototype/tests/test_formal_experiment_queue.py`

- [ ] **Step 1: Write the failing test**

```python
def test_label_batch_output_name_paths_are_isolated(self) -> None:
    from run_label_sanity_batch import label_batch_output_paths

    paths = label_batch_output_paths("formal_e1_label_sanity")

    self.assertEqual(paths["summary_csv"].name, "formal_e1_label_sanity_label_sanity_batch_summary.csv")
    self.assertEqual(paths["summary_json"].name, "formal_e1_label_sanity_label_sanity_batch_summary.json")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest sim/prototype/tests/test_formal_experiment_queue.py
```

Expected: FAIL because `label_batch_output_paths` is not defined.

- [ ] **Step 3: Write minimal implementation**

Add `label_batch_output_paths(output_name: str | None = None)` to `run_label_sanity_batch.py`. If `output_name` is missing, keep current filenames. If it is provided, prefix the two summary files with `{output_name}_`.

- [ ] **Step 4: Update batch writer**

Use `label_batch_output_paths(output_name)` inside `run_batch`, add an optional `output_name: str | None = None` parameter, and expose `--output-name` in the CLI.

- [ ] **Step 5: Run test to verify it passes**

Run:

```powershell
python -m unittest sim/prototype/tests/test_formal_experiment_queue.py
```

Expected: PASS.

### Task 2: Formal Queue Job Builder

**Files:**
- Create: `sim/prototype/src/run_formal_experiment_queue.py`
- Modify: `sim/prototype/tests/test_formal_experiment_queue.py`

- [ ] **Step 1: Write the failing test**

```python
def test_build_default_queue_contains_planned_formal_jobs(self) -> None:
    from run_formal_experiment_queue import build_default_jobs

    jobs = build_default_jobs(config_path="cfg.json")
    job_ids = [job.job_id for job in jobs]

    self.assertEqual(job_ids, [
        "E1_label_event_sanity",
        "E2_main_closed_loop_screening",
        "A1_fairness_weight_0_0",
        "A1_fairness_weight_0_15",
        "A1_fairness_weight_0_3",
        "A1_fairness_weight_0_5",
        "A2_max_release_1",
        "A2_max_release_2",
        "A2_max_release_3",
        "A3_safe_gap_0_8",
        "A3_safe_gap_1_2",
        "A3_safe_gap_1_6",
    ])
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest sim/prototype/tests/test_formal_experiment_queue.py
```

Expected: FAIL because `run_formal_experiment_queue` is not defined.

- [ ] **Step 3: Write minimal implementation**

Create `ExperimentJob` dataclass and `build_default_jobs(config_path: str)` with the fixed queue from `docs/experiments/formal_experiment_design_20260617.md`.

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest sim/prototype/tests/test_formal_experiment_queue.py
```

Expected: PASS.

### Task 3: Manifest Dry Run

**Files:**
- Modify: `sim/prototype/src/run_formal_experiment_queue.py`
- Modify: `sim/prototype/tests/test_formal_experiment_queue.py`

- [ ] **Step 1: Write the failing test**

```python
def test_write_manifest_records_commands_without_results(self) -> None:
    from run_formal_experiment_queue import build_default_jobs, write_manifest

    with tempfile.TemporaryDirectory() as tmp:
        manifest = write_manifest(build_default_jobs("cfg.json")[:2], Path(tmp) / "manifest.json")
        payload = json.loads(manifest.read_text(encoding="utf-8"))

    self.assertEqual(payload["status"], "planned")
    self.assertEqual(payload["job_count"], 2)
    self.assertEqual(payload["jobs"][0]["job_id"], "E1_label_event_sanity")
    self.assertIn("TBD", payload["no_fabrication_note"])
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest sim/prototype/tests/test_formal_experiment_queue.py
```

Expected: FAIL because `write_manifest` is not defined.

- [ ] **Step 3: Write minimal implementation**

Add `write_manifest(jobs, path, status="planned")` that serializes job IDs, group, backend, parameters, command strings, expected outputs, and a no-fabrication note.

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest sim/prototype/tests/test_formal_experiment_queue.py
```

Expected: PASS.

### Task 4: Optional Job Execution

**Files:**
- Modify: `sim/prototype/src/run_formal_experiment_queue.py`
- Modify: `sim/prototype/tests/test_formal_experiment_queue.py`

- [ ] **Step 1: Write the failing test**

```python
def test_run_selected_jobs_uses_backend_functions(self) -> None:
    from run_formal_experiment_queue import build_default_jobs, run_selected_jobs

    jobs = build_default_jobs("cfg.json")[:2]
    calls = []

    def fake_label(**kwargs):
        calls.append(("label", kwargs["output_name"]))
        return {"summary_json": "label.json"}

    def fake_closed_loop(**kwargs):
        calls.append(("closed", kwargs["output_name"]))
        return {"summary": "closed.json"}

    results = run_selected_jobs(
        jobs,
        selected_job_ids=["E1_label_event_sanity", "E2_main_closed_loop_screening"],
        label_runner=fake_label,
        closed_loop_runner=fake_closed_loop,
    )

    self.assertEqual(calls, [
        ("label", "formal_e1_label_event_sanity"),
        ("closed", "formal_e2_main_screen_tj_routezone_seed1_5_lmh_pen20_50_80_d120"),
    ])
    self.assertEqual([item["status"] for item in results], ["completed", "completed"])
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest sim/prototype/tests/test_formal_experiment_queue.py
```

Expected: FAIL because `run_selected_jobs` is not defined.

- [ ] **Step 3: Write minimal implementation**

Add `run_selected_jobs` with injectable backend functions for tests. Use real `run_label_sanity_batch.run_batch` and `run_closed_loop_batch.run_batch` by default.

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m unittest sim/prototype/tests/test_formal_experiment_queue.py
```

Expected: PASS.

### Task 5: CLI And Verification

**Files:**
- Modify: `sim/prototype/src/run_formal_experiment_queue.py`
- Modify: `docs/experiments/formal_experiment_design_20260617.md`

- [ ] **Step 1: Add CLI**

Expose:

```powershell
python sim/prototype/src/run_formal_experiment_queue.py --dry-run
python sim/prototype/src/run_formal_experiment_queue.py --run E1_label_event_sanity
python sim/prototype/src/run_formal_experiment_queue.py --run-group E2
```

- [ ] **Step 2: Document the queue command**

Add a short "Formal Queue Runner" section to the experiment design document with dry-run and selected-run examples.

- [ ] **Step 3: Run focused tests**

Run:

```powershell
python -m unittest sim/prototype/tests/test_formal_experiment_queue.py
```

Expected: all tests pass.

- [ ] **Step 4: Run full prototype tests**

Run:

```powershell
python -m unittest discover sim/prototype/tests
```

Expected: all tests pass.

- [ ] **Step 5: Generate dry-run manifest**

Run:

```powershell
python sim/prototype/src/run_formal_experiment_queue.py --dry-run
```

Expected: a JSON manifest under `sim/prototype/reports/formal_experiment_queue_manifest.json` with 12 planned jobs and no fabricated result values.

- [ ] **Step 6: Commit and push**

```powershell
git add docs/superpowers/plans/2026-06-17-formal-experiment-queue.md sim/prototype/src/run_label_sanity_batch.py sim/prototype/src/run_formal_experiment_queue.py sim/prototype/tests/test_formal_experiment_queue.py docs/experiments/formal_experiment_design_20260617.md
git commit -m "feat: add formal experiment queue runner"
git push
```
