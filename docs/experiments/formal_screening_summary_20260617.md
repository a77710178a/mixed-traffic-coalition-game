# Formal Screening Summary

Date: 2026-06-17

Scope: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized coalition allocation.

This summary consolidates completed screening experiments. It does not make final paper claims.

## Completed Runs

| Stage | Runs | Purpose | Report |
| --- | ---: | --- | --- |
| E1 | 45 | Label/event sanity | `docs/experiments/formal_e1_label_sanity_report_20260617.md` |
| E2 | 135 | Main closed-loop screening | `docs/experiments/formal_e2_closed_loop_screening_report_20260617.md` |
| A1 | 40 | Fairness weight ablation | `docs/experiments/formal_a1_fairness_ablation_report_20260617.md` |
| A2 | 30 | Coalition size ablation | `docs/experiments/formal_a2_coalition_size_ablation_report_20260617.md` |
| A3 | 30 | Safe arrival gap ablation | `docs/experiments/formal_a3_safe_gap_ablation_report_20260617.md` |
| J1 | 80 | Joint tuning sweep | `docs/experiments/formal_j1_joint_tuning_report_20260617.md` |
| R1 | 90 | Selected-candidate re-screening | `docs/experiments/formal_rescreen_selected_candidate_report_20260618.md` |
| S1-S4 | 180 | Safety-constrained candidate screen | `docs/experiments/formal_safety_constrained_candidate_screen_report_20260618.md` |
| Total | 630 | Screening and mechanism diagnosis | this summary |

Runs through J1 were executed locally in the Codex workspace. R1 and S1-S4 were executed on the remote server under the remote-only policy for heavy simulations.

## What We Know

### Data Validity

E1 confirms that the route-zone geometry produces usable event and label data:

- 45 runs
- 3374 route-zone events
- 1193 yield labels
- 1191 high-confidence labels

This is enough to proceed with closed-loop screening and later prediction-model experiments. High-CAV-penetration settings naturally produce fewer HDV-priority labels, so learned HDV-priority claims should be scoped carefully.

### Main Method Signal

E2 shows that the current coalition mechanism has an efficiency signal but not yet a clean safety/fairness result:

| Method | Runs | Throughput ↑ | Mean travel time ↓ | Near conflicts ↓ | Mean PET ↑ | Waiting Gini ↓ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `fcfs` | 45 | 12.20 | 57.40 | 0.33 | 41.92 | 0.5994 |
| `prediction_fcfs` | 45 | 12.20 | 57.40 | 0.33 | 41.92 | 0.5994 |
| `prediction_coalition` | 45 | 13.07 | 54.81 | 0.47 | 38.81 | 0.6066 |

Relative to `fcfs`, `prediction_coalition` improved throughput by 7.10% and reduced mean travel time by 4.52%, but increased near-conflict count and reduced PET.

### Mechanism Diagnosis

A2 shows that coalition size is a major efficiency-safety knob:

- `max_release_count=3`: strongest efficiency, weak PET.
- `max_release_count=2`: more balanced; similar near-conflict count to matched FCFS and better PET than release count 3.
- `max_release_count=1`: too conservative, lower throughput than matched FCFS.

A3 shows that safe gap is not monotonic under the current release logic:

- `safe_arrival_gap_s=0.8` gave the best aggregate efficiency/PET balance in the tested sub-workload.
- `safe_arrival_gap_s=1.6` reduced throughput and did not recover PET.
- This parameter interacts with ordering and HDV close-arrival blocking, so it should be tuned jointly with coalition size.

A1 shows that the fairness weight currently behaves more like a regularizer:

- Higher fairness weights reduce near-conflict counts.
- Waiting Gini improves only slightly.
- Mean/max waiting time does not improve.
- Efficiency decreases as fairness weight increases.

## What We Cannot Claim Yet

Do not claim any of the following yet:

- "The proposed method is safer than FCFS."
- "The fairness term substantially improves fairness."
- "Larger safe gap always improves safety."
- "Prediction alone improves closed-loop behavior."
- "The current default parameters are final."

The current evidence supports a narrower claim:

```text
Route-zone coalition allocation can produce an efficiency gain in a T-junction mixed-traffic prototype, but the release-set and fairness/safety parameters must be tuned jointly to avoid PET and near-conflict regressions.
```

## Current Best Candidate Settings

Based on completed screening and the completed J1 joint tuning sweep:

| Candidate | Why |
| --- | --- |
| `max_release_count=3`, `safe_arrival_gap_s=0.8`, `fairness_weight=0.3` | Selected J1 candidate: near-conflict count matches matched FCFS, PET is slightly higher than matched FCFS, and throughput/travel time improve |
| `max_release_count=2`, `safe_arrival_gap_s=1.2`, `fairness_weight=0.15` | Conservative fallback with strong PET but weaker throughput |
| `max_release_count=3`, `safe_arrival_gap_s=0.8`, `fairness_weight=0.15` | Higher-throughput candidate rejected for now because near-conflict count increases |

## Completed Joint Sweep

The compact joint tuning sweep was run as queue group `J1`:

```text
max_release_count in {2, 3}
safe_arrival_gap_s in {0.8, 1.2}
fairness_weight in {0.15, 0.3}
volumes = medium, high
penetration = 0.5
seeds = 1..5
duration = 120 s
```

This was 8 settings x 10 runs = 80 runs.

J1 selected:

```text
max_release_count = 3
safe_arrival_gap_s = 0.8
fairness_weight = 0.3
```

Matched against the FCFS subset, the selected candidate produced:

```text
throughput: 10.50 vs 10.10
mean travel time: 64.59 s vs 67.91 s
near-conflict count: 0.20 vs 0.20
min PET: 22.69 s vs 21.24 s
mean PET: 48.78 s vs 47.58 s
waiting Gini: 0.5554 vs 0.5499
```

## Completed Selected-Candidate Re-Screening

The E2-style re-screening with the selected candidate has been completed on the remote server:

```text
seeds = 1..5
volumes = low, medium, high
penetrations = 0.2, 0.5, 0.8
duration = 120 s
methods = fcfs, selected coalition
selected coalition = max_release_count 3, safe_arrival_gap_s 0.8, fairness_weight 0.3
```

The selected candidate reduced mean observed travel time from 57.40 s to 54.80 s and improved average throughput from 12.20 to 12.56 vehicles/run, but it worsened waiting Gini, conflict-pair count, near-conflict count, and PET in the aggregate table.

This result did not justify a final 300 s confirmatory run with the exact selected candidate. The follow-up safety-constrained candidate screen tested four less aggressive or more regularized coalition variants while reusing the completed FCFS reference.

## Current Balanced Candidate

The safety-constrained screen promotes S3 as the current balanced confirmatory candidate:

```text
max_release_count = 2
safe_arrival_gap_s = 1.2
fairness_weight = 0.15
```

Compared with the same 45-run FCFS reference, S3 produced:

```text
throughput: 12.04 vs 12.20
mean travel time: 56.26 s vs 57.40 s
near-conflict count: 0.36 vs 0.33
min PET: 13.48 s vs 13.40 s
mean PET: 42.95 s vs 41.92 s
waiting Gini: 0.6048 vs 0.5994
```

S3 is not a safety-superiority result, but it is a better balanced confirmatory candidate than the original R1 setting because it recovers PET while preserving a modest travel-time benefit.

S2 remains the conservative backup:

```text
max_release_count = 2
safe_arrival_gap_s = 1.2
fairness_weight = 0.3
```

Next, run a smaller 300 s pilot before full confirmatory experiments:

```text
methods = fcfs, S3
seeds = 1,2,3
volumes = medium, high
penetrations = 0.5, 0.8
duration = 300 s
```

## Remote Server Use

Current screening runs were local and caused noticeable laptop slowdown. From this point onward, all closed-loop batch experiments should run on the remote server. See `docs/experiments/remote_execution_policy_20260617.md`.

Use the remote server for:

- 300 s confirmatory runs,
- 10-seed or larger sweeps,
- deep learning predictor training,
- repeated robustness runs.

The remote server is not needed for the completed screening stage.
