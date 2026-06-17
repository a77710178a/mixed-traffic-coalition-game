# Joint Tuning Sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add and run the J1 joint tuning sweep for coalition size, safe arrival gap, and fairness weight.

**Architecture:** Extend the existing `run_formal_experiment_queue.py` queue builder with a small J1 job group. Reuse the existing closed-loop batch backend, manifest writer, and queue CLI so the sweep can be dry-run, executed, and audited like E1/E2/A1/A2/A3.

**Tech Stack:** Python standard library, existing `run_closed_loop_batch.py`, existing `run_formal_experiment_queue.py`, `unittest`.

---

### Task 1: Add J1 Queue Jobs

**Files:**
- Modify: `sim/prototype/tests/test_formal_experiment_queue.py`
- Modify: `sim/prototype/src/run_formal_experiment_queue.py`

- [ ] **Step 1: Write the failing test**

```python
def test_build_default_queue_contains_joint_tuning_jobs(self) -> None:
    from run_formal_experiment_queue import build_default_jobs

    jobs = [job for job in build_default_jobs(config_path="cfg.json") if job.group == "J1"]
    job_ids = [job.job_id for job in jobs]

    self.assertEqual(
        job_ids,
        [
            "J1_mr2_gap0_8_fw0_15",
            "J1_mr2_gap0_8_fw0_3",
            "J1_mr2_gap1_2_fw0_15",
            "J1_mr2_gap1_2_fw0_3",
            "J1_mr3_gap0_8_fw0_15",
            "J1_mr3_gap0_8_fw0_3",
            "J1_mr3_gap1_2_fw0_15",
            "J1_mr3_gap1_2_fw0_3",
        ],
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest sim/prototype/tests/test_formal_experiment_queue.py
```

Expected: FAIL because no J1 jobs exist.

- [ ] **Step 3: Implement the minimal queue extension**

Add helper token formatting for floats if useful, then append 8 J1 `ExperimentJob` entries after A3 with:

```python
max_release_count in [2, 3]
safe_arrival_gap_s in [0.8, 1.2]
fairness_weight in [0.15, 0.3]
seeds=[1, 2, 3, 4, 5]
volumes=["medium", "high"]
penetrations=[0.5]
methods=["prediction_coalition"]
duration=120.0
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m unittest sim/prototype/tests/test_formal_experiment_queue.py
```

Expected: PASS.

### Task 2: Verify Manifest And Full Tests

**Files:**
- Modify: `docs/experiments/formal_screening_summary_20260617.md`

- [ ] **Step 1: Run dry-run**

Run:

```powershell
python sim/prototype/src/run_formal_experiment_queue.py --dry-run
```

Expected: manifest reports 20 planned jobs: E1, E2, A1 x4, A2 x3, A3 x3, J1 x8.

- [ ] **Step 2: Run full tests**

Run:

```powershell
python -m unittest discover sim/prototype/tests
```

Expected: all tests pass.

- [ ] **Step 3: Update summary**

Add a short note to `formal_screening_summary_20260617.md` that J1 is now represented in the queue runner as the next sweep.

- [ ] **Step 4: Commit and push**

```powershell
git add docs/superpowers/plans/2026-06-17-joint-tuning-sweep.md sim/prototype/src/run_formal_experiment_queue.py sim/prototype/tests/test_formal_experiment_queue.py docs/experiments/formal_screening_summary_20260617.md
git commit -m "feat: add joint tuning sweep queue"
git push
```

### Task 3: Run J1 And Report

**Files:**
- Create: `docs/experiments/formal_j1_joint_tuning_report_20260617.md`
- Modify: `docs/experiments/formal_screening_summary_20260617.md`

- [ ] **Step 1: Execute J1**

Run:

```powershell
python sim/prototype/src/run_formal_experiment_queue.py --run-group J1
```

Expected: 8 jobs complete, 80 closed-loop runs total.

- [ ] **Step 2: Aggregate verified results**

Read each J1 `closed_loop_batch_aggregate.csv`, compare against the matched FCFS subset from E2, and rank candidates by:

1. near-conflict count no worse than matched FCFS by more than a small tolerance,
2. mean PET close to matched FCFS,
3. throughput improvement over matched FCFS,
4. waiting Gini not substantially worse.

- [ ] **Step 3: Write the J1 report**

Create a report with:

- protocol table,
- matched FCFS reference row,
- all 8 J1 candidate rows,
- selected candidate,
- rejected candidates and reasons,
- next E2-style re-screening command.

- [ ] **Step 4: Verify, commit, and push**

Run:

```powershell
python -m unittest discover sim/prototype/tests
git add docs/experiments/formal_j1_joint_tuning_report_20260617.md docs/experiments/formal_screening_summary_20260617.md
git commit -m "docs: record formal j1 joint tuning sweep"
git push
```
