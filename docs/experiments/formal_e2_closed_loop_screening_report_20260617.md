# E2 Closed-Loop Screening Report

Date: 2026-06-17

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

Command:

```powershell
python sim/prototype/src/run_formal_experiment_queue.py --run E2_main_closed_loop_screening
```

Generated artifacts:

- `sim/prototype/reports/formal_e2_main_screen_tj_routezone_seed1_5_lmh_pen20_50_80_d120/closed_loop_batch_runs.csv`
- `sim/prototype/reports/formal_e2_main_screen_tj_routezone_seed1_5_lmh_pen20_50_80_d120/closed_loop_batch_aggregate.csv`
- `sim/prototype/reports/formal_e2_main_screen_tj_routezone_seed1_5_lmh_pen20_50_80_d120/closed_loop_batch_summary.json`

These artifacts are local generated outputs and are intentionally ignored by Git. This document records only verified aggregate values from that completed run.

## Protocol

| Setting | Value |
| --- | --- |
| Seeds | 1, 2, 3, 4, 5 |
| Volumes | low, medium, high |
| CAV penetrations | 0.2, 0.5, 0.8 |
| Methods | `fcfs`, `prediction_fcfs`, `prediction_coalition` |
| Duration | 120 s |
| Runs | 135 |
| Geometry mode | route zones |
| Fairness weight | 0.15 |
| Max release count | 3 |
| Safe arrival gap | 1.2 s |
| Near-conflict PET threshold | 1.5 s |

## Main Aggregate

| Method | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Max wait ↓ | Stop proxy ↓ | Waiting Gini ↓ | Conflict pairs ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fcfs` | 45 | 12.20 | 57.40 | 25.55 | 87.57 | 29.49 | 0.5994 | 23.40 | 0.33 | 13.40 | 41.92 |
| `prediction_fcfs` | 45 | 12.20 | 57.40 | 25.55 | 87.57 | 29.49 | 0.5994 | 23.40 | 0.33 | 13.40 | 41.92 |
| `prediction_coalition` | 45 | 13.07 | 54.81 | 27.18 | 90.88 | 29.47 | 0.6066 | 26.80 | 0.47 | 10.00 | 38.81 |

Relative to `fcfs`, `prediction_coalition` produced:

| Metric | Change |
| --- | ---: |
| Throughput | +0.87 vehicles/run (+7.10%) |
| Mean travel time | -2.59 s (-4.52%) |
| Mean max wait | +1.64 s |
| Waiting Gini | +0.0072 |
| Conflict pairs | +3.40 pairs/run |
| Near conflicts | +0.13 events/run |
| Mean PET | -3.11 s |

## By Demand Level

| Volume | Method | Runs | Throughput ↑ | Mean travel time ↓ | Near conflicts ↓ | Mean PET ↑ | Waiting Gini ↓ |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| low | `fcfs` | 15 | 11.67 | 45.27 | 0.07 | 40.18 | 0.6698 |
| low | `prediction_fcfs` | 15 | 11.67 | 45.27 | 0.07 | 40.18 | 0.6698 |
| low | `prediction_coalition` | 15 | 13.20 | 41.84 | 0.27 | 35.45 | 0.6837 |
| medium | `fcfs` | 15 | 12.07 | 59.33 | 0.40 | 46.33 | 0.5675 |
| medium | `prediction_fcfs` | 15 | 12.07 | 59.33 | 0.40 | 46.33 | 0.5675 |
| medium | `prediction_coalition` | 15 | 12.73 | 56.40 | 0.47 | 42.39 | 0.5759 |
| high | `fcfs` | 15 | 12.87 | 67.61 | 0.53 | 39.53 | 0.5609 |
| high | `prediction_fcfs` | 15 | 12.87 | 67.61 | 0.53 | 39.53 | 0.5609 |
| high | `prediction_coalition` | 15 | 13.27 | 66.18 | 0.67 | 38.54 | 0.5603 |

## By CAV Penetration

| CAV penetration | Method | Runs | Throughput ↑ | Mean travel time ↓ | Near conflicts ↓ | Mean PET ↑ | Waiting Gini ↓ |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.2 | `fcfs` | 15 | 19.00 | 47.85 | 0.87 | 33.94 | 0.6717 |
| 0.2 | `prediction_fcfs` | 15 | 19.00 | 47.85 | 0.87 | 33.94 | 0.6717 |
| 0.2 | `prediction_coalition` | 15 | 19.13 | 46.21 | 1.07 | 34.00 | 0.6705 |
| 0.5 | `fcfs` | 15 | 9.80 | 62.22 | 0.13 | 46.94 | 0.5648 |
| 0.5 | `prediction_fcfs` | 15 | 9.80 | 62.22 | 0.13 | 46.94 | 0.5648 |
| 0.5 | `prediction_coalition` | 15 | 11.27 | 59.24 | 0.20 | 40.94 | 0.5707 |
| 0.8 | `fcfs` | 15 | 7.80 | 62.13 | 0.00 | 45.21 | 0.5616 |
| 0.8 | `prediction_fcfs` | 15 | 7.80 | 62.13 | 0.00 | 45.21 | 0.5616 |
| 0.8 | `prediction_coalition` | 15 | 8.80 | 58.98 | 0.13 | 41.82 | 0.5786 |

## Interpretation

The E2 screening shows an initial efficiency signal but not yet a paper-ready safety/fairness result:

- `prediction_coalition` improved throughput and mean travel time relative to `fcfs`.
- The improvement is driven by coalition release-set behavior, because `prediction_fcfs` matched `fcfs` under the current heuristic predictor and release policy.
- The current default coalition setting increases conflict-pair counts and near-conflict counts, and reduces PET. This means the current `max_release_count=3` and `safe_arrival_gap_s=1.2` should not be treated as final.
- Fairness is not improved at this default setting; mean max wait and Gini are slightly worse overall.
- The next experiments should prioritize release-set and safety-constraint tuning before making any strong method claim.

## Next Experiment Decision

Proceed to mechanism ablations before confirmatory 300 s runs:

1. A2 coalition size: `max_release_count = 1, 2, 3`
2. A3 safe arrival gap: `safe_arrival_gap_s = 0.8, 1.2, 1.6`
3. A1 fairness weight: `fairness_weight = 0.0, 0.15, 0.3, 0.5`

The immediate target is to find a conservative coalition configuration that preserves most of the efficiency gain while reducing near-conflict and PET regressions.

No final paper superiority claim is made by this report.
