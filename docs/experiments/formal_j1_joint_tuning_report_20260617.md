# J1 Joint Tuning Sweep Report

Date: 2026-06-17

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

Command:

```powershell
python sim/prototype/src/run_formal_experiment_queue.py --run-group J1
```

Generated artifacts:

- `sim/prototype/reports/joint_j1_mr2_gap0_8_fw0_15_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/joint_j1_mr2_gap0_8_fw0_3_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/joint_j1_mr2_gap1_2_fw0_15_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/joint_j1_mr2_gap1_2_fw0_3_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/joint_j1_mr3_gap0_8_fw0_15_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/joint_j1_mr3_gap0_8_fw0_3_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/joint_j1_mr3_gap1_2_fw0_15_tj_seed1_5_mh_pen50_d120/`
- `sim/prototype/reports/joint_j1_mr3_gap1_2_fw0_3_tj_seed1_5_mh_pen50_d120/`

These artifacts are local generated outputs and are intentionally ignored by Git. This document records only verified aggregate values from completed runs.

## Protocol

| Setting | Value |
| --- | --- |
| Seeds | 1, 2, 3, 4, 5 |
| Volumes | medium, high |
| CAV penetration | 0.5 |
| Method | `prediction_coalition` |
| Duration | 120 s |
| Max release count | 2, 3 |
| Safe arrival gap | 0.8, 1.2 s |
| Fairness weight | 0.15, 0.3 |
| Runs | 80 |

For context, the matched FCFS subset from E2 has 10 runs under the same seed, volume, penetration, and duration settings.

## Matched Reference

| Reference | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Max wait ↓ | Waiting Gini ↓ | Conflict pairs ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| matched `fcfs` | 10 | 10.10 | 67.91 | 31.20 | 98.36 | 0.5499 | 13.90 | 0.20 | 21.24 | 47.58 |
| previous default coalition | 10 | 11.30 | 64.61 | 35.37 | 100.20 | 0.5498 | 18.00 | 0.30 | 7.93 | 39.67 |

## Candidate Results

| Candidate | Max release | Safe gap | Fairness weight | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Waiting Gini ↓ | Conflict pairs ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `mr2_gap0.8_fw0.15` | 2 | 0.8 | 0.15 | 10 | 10.00 | 65.83 | 34.63 | 0.5455 | 17.20 | 0.20 | 21.32 | 48.98 |
| `mr2_gap0.8_fw0.3` | 2 | 0.8 | 0.30 | 10 | 9.70 | 66.38 | 34.52 | 0.5448 | 16.90 | 0.20 | 22.39 | 50.05 |
| `mr2_gap1.2_fw0.15` | 2 | 1.2 | 0.15 | 10 | 9.80 | 66.22 | 34.41 | 0.5462 | 16.50 | 0.20 | 22.47 | 48.92 |
| `mr2_gap1.2_fw0.3` | 2 | 1.2 | 0.30 | 10 | 9.80 | 66.61 | 34.16 | 0.5479 | 16.50 | 0.20 | 22.51 | 49.03 |
| `mr3_gap0.8_fw0.15` | 3 | 0.8 | 0.15 | 10 | 11.40 | 63.63 | 34.77 | 0.5566 | 20.10 | 0.40 | 21.89 | 47.17 |
| `mr3_gap0.8_fw0.3` | 3 | 0.8 | 0.30 | 10 | 10.50 | 64.59 | 35.03 | 0.5554 | 19.10 | 0.20 | 22.69 | 48.78 |
| `mr3_gap1.2_fw0.15` | 3 | 1.2 | 0.15 | 10 | 11.30 | 64.61 | 35.37 | 0.5498 | 18.00 | 0.30 | 7.93 | 39.67 |
| `mr3_gap1.2_fw0.3` | 3 | 1.2 | 0.30 | 10 | 10.40 | 64.95 | 35.49 | 0.5494 | 16.90 | 0.20 | 10.71 | 40.51 |

## By Demand For Selected Candidate

Selected candidate: `max_release_count=3`, `safe_arrival_gap_s=0.8`, `fairness_weight=0.3`.

| Volume | Method / candidate | Runs | Throughput ↑ | Mean travel time ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ | Waiting Gini ↓ |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| medium | matched `fcfs` | 5 | 10.60 | 62.69 | 0.00 | 21.70 | 51.49 | 0.5496 |
| medium | selected candidate | 5 | 9.60 | 61.15 | 0.00 | 24.02 | 52.73 | 0.5515 |
| high | matched `fcfs` | 5 | 9.60 | 73.14 | 0.40 | 20.88 | 44.45 | 0.5502 |
| high | selected candidate | 5 | 11.40 | 68.03 | 0.40 | 21.62 | 45.62 | 0.5592 |

## Selection

The selected candidate is:

```text
max_release_count = 3
safe_arrival_gap_s = 0.8
fairness_weight = 0.3
```

Why selected:

- Near-conflict count matches the matched FCFS subset: 0.20 vs 0.20.
- Mean PET is slightly higher than matched FCFS: 48.78 s vs 47.58 s.
- Min PET is slightly higher than matched FCFS: 22.69 s vs 21.24 s.
- Throughput improves over matched FCFS: 10.50 vs 10.10 vehicles/run.
- Mean travel time improves over matched FCFS: 64.59 s vs 67.91 s.

Known tradeoff:

- Waiting Gini is slightly worse than matched FCFS: 0.5554 vs 0.5499.
- Conflict-pair count remains higher than matched FCFS: 19.10 vs 13.90.
- Medium-demand throughput is lower than matched FCFS, while high-demand throughput is higher.

## Rejected Candidates

- `mr3_gap0.8_fw0.15`: best throughput, but near-conflict count increases from 0.20 to 0.40.
- `mr3_gap1.2_fw0.15`: strong throughput, but PET collapses relative to matched FCFS.
- `mr3_gap1.2_fw0.3`: near-conflict count is acceptable, but PET remains much lower than matched FCFS.
- `mr2_*`: PET is strong, but throughput is at or below matched FCFS in this workload.

## Next Step

Run an E2-style re-screening with the selected candidate before any 300 s confirmatory runs:

```powershell
python sim/prototype/src/run_closed_loop_batch.py `
  --config sim/prototype/config/t_junction_scenario.json `
  --seeds 1,2,3,4,5 `
  --volumes low,medium,high `
  --penetrations 0.2,0.5,0.8 `
  --methods fcfs,prediction_coalition `
  --duration 120 `
  --control-radius-m 45 `
  --fairness-weight 0.3 `
  --max-release-count 3 `
  --safe-arrival-gap-s 0.8 `
  --near-conflict-pet-s 1.5 `
  --output-name formal_rescreen_selected_mr3_gap08_fw03_seed1_5_lmh_pen20_50_80_d120
```

Given runtime on the local machine, this re-screening and later 300 s confirmatory runs should be moved to the remote server.

No final paper superiority claim is made by this report.
