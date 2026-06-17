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
| Total | 280 | Screening and mechanism diagnosis | this summary |

All runs above were executed locally in the Codex workspace, not on the remote server.

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

Based on completed screening:

| Candidate | Why |
| --- | --- |
| `max_release_count=2`, `safe_arrival_gap_s=1.2`, `fairness_weight=0.15` | Balanced A2 candidate with stronger PET than release count 3 |
| `max_release_count=3`, `safe_arrival_gap_s=0.8`, `fairness_weight=0.15` | Strong A3 efficiency/PET candidate, but high-demand near-conflict needs checking |
| `max_release_count=3`, `safe_arrival_gap_s=1.2`, `fairness_weight=0.3` | A1 safety-regularized candidate with fewer near-conflicts but weaker efficiency |

## Next Required Sweep

Before any 300 s confirmatory runs, run the compact joint tuning sweep now represented as queue group `J1`:

```text
max_release_count in {2, 3}
safe_arrival_gap_s in {0.8, 1.2}
fairness_weight in {0.15, 0.3}
volumes = medium, high
penetration = 0.5
seeds = 1..5
duration = 120 s
```

This is 8 settings x 10 runs = 80 runs.

Primary selection rule:

1. Near-conflict count should be no worse than matched FCFS by more than a small tolerance.
2. Mean PET should be close to matched FCFS.
3. Throughput should improve over matched FCFS.
4. Waiting Gini should not degrade substantially.

After selecting one candidate, rerun E2-style main screening with the selected parameters across:

```text
seeds = 1..5
volumes = low, medium, high
penetrations = 0.2, 0.5, 0.8
duration = 120 s
methods = fcfs, selected coalition
```

Only after that should we decide whether a 300 s, 10-seed confirmatory experiment is justified.

## Remote Server Use

Current screening runs were local. Use the remote server for:

- 300 s confirmatory runs,
- 10-seed or larger sweeps,
- deep learning predictor training,
- repeated robustness runs.

The remote server is not needed for the completed screening stage.
