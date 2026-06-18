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
| P1 | 24 | S3 300 s pilot | `docs/experiments/formal_pilot_s3_300s_report_20260618.md` |
| P2 | 48 | CAV waiting tie-breaker 300 s pilot | `docs/experiments/formal_pilot_wait_tiebreaker_300s_report_20260618.md` |
| P3 | 24 | Adaptive release gate 300 s pilot | `docs/experiments/formal_pilot_adaptive_gate_300s_report_20260618.md` |
| P4 | 48 | Adaptive conflict-gap sensitivity | `docs/experiments/formal_pilot_adaptive_gap_sensitivity_300s_report_20260618.md` |
| Total | 774 | Screening and mechanism diagnosis | this summary |

Runs through J1 were executed locally in the Codex workspace. R1, S1-S4, P1, P2, P3, and P4 were executed on the remote server under the remote-only policy for heavy simulations.

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

The 300 s pilot has now been completed:

```text
methods = fcfs, S3
seeds = 1,2,3
volumes = medium, high
penetrations = 0.5, 0.8
duration = 300 s
```

P1 result:

```text
throughput: 30.25 vs 31.42
mean travel time: 158.62 s vs 158.33 s
near-conflict count: 0.42 vs 0.50
min PET: 3.41 s vs 3.34 s
mean PET: 92.41 s vs 89.77 s
waiting Gini: 0.6269 vs 0.6279
```

This pilot does not support S3 as an efficiency-improving final default under longer simulation. It supports S3 as a safety-leaning conservative variant: near conflicts, mean PET, min PET, and waiting Gini improve slightly, but throughput and travel time do not.

The follow-up P2 pilot tested this adjustment:

```text
max_release_count = 2
safe_arrival_gap_s = 1.2
cav_waiting_tiebreaker_weight = 0.1
fairness_weight in {0.0, 0.1}
duration = 300 s
runs = 48
```

P2 result:

```text
FCFS throughput: 31.42
S3 throughput: 30.25
W0 throughput: 30.25
W1 throughput: 30.25

FCFS mean travel time: 158.33 s
S3 mean travel time: 158.62 s
W0 mean travel time: 156.75 s
W1 mean travel time: 158.52 s

FCFS mean PET: 89.77 s
S3 mean PET: 92.41 s
W0 mean PET: 92.61 s
W1 mean PET: 92.28 s
```

P2 shows that the CAV waiting tie-breaker improves W0 travel time and preserves the S3 PET/near-conflict behavior, but it does not recover throughput. This suggests the bottleneck is not mainly the fairness ordering; it is the release eligibility structure itself.

P3 tested a geometry-aware adaptive release gate:

```text
base max_release_count = 2
adaptive_max_release_count = 3
safe_arrival_gap_s = 1.2
adaptive_min_conflict_arrival_gap_s = 2.4
adaptive_max_occupancy = 0
fairness_weight = 0.0
cav_waiting_tiebreaker_weight = 0.1
duration = 300 s
runs = 24
```

P3 result:

```text
FCFS throughput: 31.42
W0 throughput: 30.25
adaptive throughput: 30.33

FCFS mean travel time: 158.33 s
W0 mean travel time: 156.75 s
adaptive mean travel time: 156.44 s

FCFS min PET: 3.34 s
W0 min PET: 3.42 s
adaptive min PET: 3.12 s

FCFS mean PET: 89.77 s
W0 mean PET: 92.61 s
adaptive mean PET: 93.31 s
```

P3 supports the adaptive release gate as a useful mechanism direction: it improves travel time and mean PET relative to W0 and gives a small throughput recovery. However, the current `adaptive_min_conflict_arrival_gap_s=2.4` setting reduces min PET, so it is not ready as the final method.

P4 tested stricter conflict-arrival gaps:

```text
adaptive_min_conflict_arrival_gap_s in {3.6, 4.0}
same 300 s protocol
runs = 48
```

P4 result:

```text
W0 throughput: 30.25
adaptive cgap=2.4 throughput: 30.33
adaptive cgap=3.6 throughput: 30.33
adaptive cgap=4.0 throughput: 30.33

W0 mean travel time: 156.75 s
adaptive cgap=2.4 mean travel time: 156.44 s
adaptive cgap=3.6 mean travel time: 156.62 s
adaptive cgap=4.0 mean travel time: 156.62 s

W0 min PET: 3.42 s
adaptive cgap=2.4 min PET: 3.12 s
adaptive cgap=3.6 min PET: 3.12 s
adaptive cgap=4.0 min PET: 3.12 s
```

P4 shows that increasing `adaptive_min_conflict_arrival_gap_s` alone does not repair the min-PET regression. The risky cases are likely passing the static conflict-route gate or being driven by a local entry-gap/PET condition not captured by the current route-conflict rule.

Do not run the full 300 s, 10-seed confirmatory experiment yet. The next method step should add an explicit extra-release safety guard, such as a projected minimum entry-gap or projected-PET threshold across all already released vehicles.

## Remote Server Use

Current screening runs were local and caused noticeable laptop slowdown. From this point onward, all closed-loop batch experiments should run on the remote server. See `docs/experiments/remote_execution_policy_20260617.md`.

Use the remote server for:

- 300 s confirmatory runs,
- 10-seed or larger sweeps,
- deep learning predictor training,
- repeated robustness runs.

The remote server is not needed for the completed screening stage.
