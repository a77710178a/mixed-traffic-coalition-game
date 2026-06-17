# A3 Safe Arrival Gap Ablation Report

Date: 2026-06-17

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

Command:

```powershell
python sim/prototype/src/run_formal_experiment_queue.py --run-group A3
```

Generated artifacts:

- `sim/prototype/reports/ablation_a3_safe_gap_0_8_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/ablation_a3_safe_gap_1_2_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/ablation_a3_safe_gap_1_6_tj_seed1_5_mh_pen50_d120/`

These artifacts are local generated outputs and are intentionally ignored by Git. This document records only verified aggregate values from completed runs.

## Protocol

| Setting | Value |
| --- | --- |
| Seeds | 1, 2, 3, 4, 5 |
| Volumes | medium, high |
| CAV penetration | 0.5 |
| Method | `prediction_coalition` |
| Duration | 120 s |
| Fairness weight | 0.15 |
| Max release count | 3 |
| Safe arrival gap | 0.8, 1.2, 1.6 s |
| Runs | 30 |

For context, the matched FCFS subset from E2 has 10 runs under the same seed, volume, penetration, and duration settings.

## Main Result

| Setting | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Max wait ↓ | Waiting Gini ↓ | Conflict pairs ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| matched `fcfs` | 10 | 10.10 | 67.91 | 31.20 | 98.36 | 0.5499 | 13.90 | 0.20 | 21.24 | 47.58 |
| safe gap 0.8 s | 10 | 11.40 | 63.63 | 34.77 | 103.19 | 0.5566 | 20.10 | 0.40 | 21.89 | 47.17 |
| safe gap 1.2 s | 10 | 11.30 | 64.61 | 35.37 | 100.20 | 0.5498 | 18.00 | 0.30 | 7.93 | 39.67 |
| safe gap 1.6 s | 10 | 10.10 | 66.80 | 35.27 | 97.50 | 0.5326 | 16.70 | 0.40 | 10.78 | 36.64 |

## By Demand Level

| Volume | Safe gap | Runs | Throughput ↑ | Mean travel time ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ | Waiting Gini ↓ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| medium | 0.8 | 5 | 10.80 | 60.23 | 0.00 | 23.90 | 51.36 | 0.5507 |
| medium | 1.2 | 5 | 12.00 | 59.11 | 0.20 | 10.22 | 44.83 | 0.5544 |
| medium | 1.6 | 5 | 10.00 | 62.12 | 0.00 | 14.76 | 40.55 | 0.5285 |
| high | 0.8 | 5 | 12.00 | 67.03 | 0.80 | 20.28 | 43.82 | 0.5625 |
| high | 1.2 | 5 | 10.60 | 70.11 | 0.40 | 5.08 | 33.23 | 0.5452 |
| high | 1.6 | 5 | 10.20 | 71.48 | 0.80 | 5.80 | 31.76 | 0.5367 |

## Interpretation

The safe-gap ablation is not monotonic under the current release-set logic:

- `safe_arrival_gap_s=0.8` has the strongest efficiency/PET balance in the aggregate table, with throughput above matched FCFS and PET close to matched FCFS.
- `safe_arrival_gap_s=1.2`, the original default, performs poorly on PET in this sub-workload.
- `safe_arrival_gap_s=1.6` reduces throughput and does not recover PET; it only improves Gini in this limited sub-workload.
- High-demand settings remain the safety stress case, especially for near-conflict counts.

This non-monotonic result suggests that `safe_arrival_gap_s` interacts with release ordering and HDV close-arrival blocking. It should not be described as a simple "larger gap is safer" parameter.

## Next Experiment Decision

The current best candidates for follow-up are:

```text
max_release_count = 2, safe_arrival_gap_s = 1.2
max_release_count = 3, safe_arrival_gap_s = 0.8
```

Before confirmatory 300 s runs, add a compact combined sweep around these candidates:

```text
max_release_count in {2, 3}
safe_arrival_gap_s in {0.8, 1.2, 1.6}
volumes = medium, high
penetration = 0.5
seeds = 1..5
duration = 120 s
```

No final paper superiority claim is made by this report.
