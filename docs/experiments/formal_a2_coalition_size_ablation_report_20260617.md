# A2 Coalition Size Ablation Report

Date: 2026-06-17

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

Command:

```powershell
python sim/prototype/src/run_formal_experiment_queue.py --run-group A2
```

Generated artifacts:

- `sim/prototype/reports/ablation_a2_max_release_1_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/ablation_a2_max_release_2_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/ablation_a2_max_release_3_tj_seed1_5_mh_pen50_d120/`

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
| Safe arrival gap | 1.2 s |
| Max release count | 1, 2, 3 |
| Runs | 30 |

For context, the matched FCFS subset from E2 has 10 runs under the same seed, volume, penetration, and duration settings.

## Main Result

| Setting | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Max wait ↓ | Waiting Gini ↓ | Conflict pairs ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| matched `fcfs` | 10 | 10.10 | 67.91 | 31.20 | 98.36 | 0.5499 | 13.90 | 0.20 | 21.24 | 47.58 |
| max release 1 | 10 | 9.00 | 69.14 | 32.19 | 100.85 | 0.5439 | 12.90 | 0.20 | 25.29 | 47.15 |
| max release 2 | 10 | 9.80 | 66.22 | 34.41 | 99.99 | 0.5462 | 16.50 | 0.20 | 22.47 | 48.92 |
| max release 3 | 10 | 11.30 | 64.61 | 35.37 | 100.20 | 0.5498 | 18.00 | 0.30 | 7.93 | 39.67 |

## By Demand Level

| Volume | Max release count | Runs | Throughput ↑ | Mean travel time ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ | Waiting Gini ↓ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| medium | 1 | 5 | 9.00 | 64.17 | 0.00 | 29.58 | 49.90 | 0.5440 |
| medium | 2 | 5 | 9.60 | 61.26 | 0.00 | 24.00 | 53.28 | 0.5503 |
| medium | 3 | 5 | 12.00 | 59.11 | 0.20 | 10.22 | 44.83 | 0.5544 |
| high | 1 | 5 | 9.00 | 74.11 | 0.40 | 21.86 | 44.96 | 0.5437 |
| high | 2 | 5 | 10.00 | 71.18 | 0.40 | 21.24 | 45.43 | 0.5421 |
| high | 3 | 5 | 10.60 | 70.11 | 0.40 | 5.08 | 33.23 | 0.5452 |

## Interpretation

The coalition size ablation confirms that release-set size is a key efficiency-safety tradeoff:

- `max_release_count=3` gives the best efficiency in this sub-workload, but it sharply reduces min PET and mean PET.
- `max_release_count=1` is too conservative: it improves conflict-pair count and min PET, but sacrifices throughput and mean travel time relative to the matched FCFS subset.
- `max_release_count=2` is the most balanced candidate so far: it improves mean travel time relative to matched FCFS and preserves near-conflict count while keeping PET much stronger than `max_release_count=3`.
- None of the A2 settings fixes waiting-time fairness by itself. Fairness still needs A1 weight tuning.

## Next Experiment Decision

Use A3 safe-gap ablation to test whether `max_release_count=2` or `3` can be made safer by increasing the arrival-gap constraint. The current queue runner tests safe gaps with `max_release_count=3`; if A3 shows that larger gaps recover PET without destroying throughput, add a follow-up combined sweep around:

```text
max_release_count in {2, 3}
safe_arrival_gap_s in {1.2, 1.6, 2.0}
```

No final paper superiority claim is made by this report.
