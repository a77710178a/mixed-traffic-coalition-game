# A1 Fairness Weight Ablation Report

Date: 2026-06-17

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

Command:

```powershell
python sim/prototype/src/run_formal_experiment_queue.py --run-group A1
```

Generated artifacts:

- `sim/prototype/reports/ablation_a1_fairness_0_0_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/ablation_a1_fairness_0_15_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/ablation_a1_fairness_0_3_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/ablation_a1_fairness_0_5_tj_seed1_5_mh_pen50_d120/`

These artifacts are local generated outputs and are intentionally ignored by Git. This document records only verified aggregate values from completed runs.

## Protocol

| Setting | Value |
| --- | --- |
| Seeds | 1, 2, 3, 4, 5 |
| Volumes | medium, high |
| CAV penetration | 0.5 |
| Method | `prediction_coalition` |
| Duration | 120 s |
| Max release count | 3 |
| Safe arrival gap | 1.2 s |
| Fairness weight | 0.0, 0.15, 0.3, 0.5 |
| Runs | 40 |

## Main Result

| Fairness weight | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Max wait ↓ | Waiting Gini ↓ | Conflict pairs ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.00 | 10 | 13.80 | 62.49 | 34.94 | 100.05 | 0.5523 | 24.70 | 0.60 | 7.76 | 41.57 |
| 0.15 | 10 | 11.30 | 64.61 | 35.37 | 100.20 | 0.5498 | 18.00 | 0.30 | 7.93 | 39.67 |
| 0.30 | 10 | 10.40 | 64.95 | 35.49 | 100.20 | 0.5494 | 16.90 | 0.20 | 10.71 | 40.51 |
| 0.50 | 10 | 10.00 | 65.25 | 35.55 | 100.32 | 0.5486 | 16.90 | 0.20 | 11.00 | 41.31 |

## By Demand Level

| Volume | Fairness weight | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ | Waiting Gini ↓ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| medium | 0.00 | 5 | 14.60 | 57.43 | 33.08 | 0.40 | 9.64 | 45.07 | 0.5536 |
| medium | 0.15 | 5 | 12.00 | 59.11 | 33.17 | 0.20 | 10.22 | 44.83 | 0.5544 |
| medium | 0.30 | 5 | 10.60 | 59.59 | 33.20 | 0.00 | 15.20 | 46.16 | 0.5530 |
| medium | 0.50 | 5 | 9.80 | 59.69 | 33.20 | 0.00 | 15.74 | 47.57 | 0.5530 |
| high | 0.00 | 5 | 13.00 | 67.55 | 36.80 | 0.80 | 5.40 | 37.20 | 0.5509 |
| high | 0.15 | 5 | 10.60 | 70.11 | 37.56 | 0.40 | 5.08 | 33.23 | 0.5452 |
| high | 0.30 | 5 | 10.20 | 70.32 | 37.78 | 0.40 | 5.10 | 33.46 | 0.5458 |
| high | 0.50 | 5 | 10.20 | 70.81 | 37.90 | 0.40 | 5.08 | 33.48 | 0.5441 |

## Interpretation

The fairness weight currently acts more like a release aggressiveness regularizer than a strong waiting-fairness mechanism:

- Increasing fairness weight from 0.0 to 0.3/0.5 reduces conflict pairs and near-conflict counts.
- Waiting Gini improves only slightly, and mean/max waiting time does not improve.
- Efficiency decreases as fairness weight increases.
- In high demand, near-conflict counts remain nonzero even with higher fairness weights.

For the current prototype, `fairness_weight=0.3` is a reasonable safety-regularized candidate, but it should not yet be claimed as a strong fairness improvement.

## Next Experiment Decision

The next compact combined sweep should test candidate settings suggested by A1/A2/A3:

```text
max_release_count in {2, 3}
safe_arrival_gap_s in {0.8, 1.2}
fairness_weight in {0.15, 0.3}
volumes = medium, high
penetration = 0.5
seeds = 1..5
duration = 120 s
```

The target is to find a configuration that preserves the efficiency gain while avoiding the PET and near-conflict regressions seen in E2.

No final paper superiority claim is made by this report.
