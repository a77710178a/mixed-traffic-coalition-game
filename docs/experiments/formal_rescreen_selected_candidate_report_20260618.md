# Selected Candidate Re-Screening Report

Date: 2026-06-18

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

This report records the E2-style re-screening of the J1 selected candidate. The run was executed on the remote server, following the remote-only policy for heavy simulations.

## Candidate

| Parameter | Value |
| --- | ---: |
| Method | `prediction_coalition` |
| Max release count | 3 |
| Safe arrival gap | 0.8 s |
| Fairness weight | 0.3 |
| Near-conflict PET threshold | 1.5 s |

## Remote Execution

Remote working directory:

```text
/public/home/xiaohei_0/hx/my_paper01/sim/prototype
```

Deployed code snapshot:

```text
9a74097
```

Command:

```bash
/public/home/xiaohei_0/conda38/bin/conda run -n sumoenv python src/run_closed_loop_batch.py \
  --config config/t_junction_scenario.json \
  --seeds 1,2,3,4,5 \
  --volumes low,medium,high \
  --penetrations 0.2,0.5,0.8 \
  --methods fcfs,prediction_coalition \
  --duration 120 \
  --control-radius-m 45 \
  --fairness-weight 0.3 \
  --max-release-count 3 \
  --safe-arrival-gap-s 0.8 \
  --near-conflict-pet-s 1.5 \
  --output-name formal_rescreen_selected_mr3_gap08_fw03_seed1_5_lmh_pen20_50_80_d120
```

Generated remote artifacts:

- `reports/formal_rescreen_selected_mr3_gap08_fw03_seed1_5_lmh_pen20_50_80_d120/closed_loop_batch_summary.json`
- `reports/formal_rescreen_selected_mr3_gap08_fw03_seed1_5_lmh_pen20_50_80_d120/closed_loop_batch_aggregate.csv`
- `reports/formal_rescreen_selected_mr3_gap08_fw03_seed1_5_lmh_pen20_50_80_d120/closed_loop_batch_runs.csv`

The summary artifacts were copied back for analysis. Generated outputs remain ignored by Git; this document records verified values only.

## Protocol

| Setting | Value |
| --- | --- |
| Seeds | 1, 2, 3, 4, 5 |
| Volumes | low, medium, high |
| CAV penetration | 0.2, 0.5, 0.8 |
| Methods | `fcfs`, selected `prediction_coalition` |
| Duration | 120 s |
| Runs | 90 |

## Aggregate Result

| Method | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Max wait ↓ | Stop proxy ↓ | Waiting Gini ↓ | Conflict pairs ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fcfs` | 45 | 12.20 | 57.40 | 25.55 | 87.57 | 29.49 | 0.5994 | 23.40 | 0.33 | 13.40 | 41.92 |
| selected `prediction_coalition` | 45 | 12.56 | 54.80 | 26.85 | 90.50 | 29.24 | 0.6113 | 26.89 | 0.38 | 12.15 | 41.39 |

Relative to `fcfs`, the selected candidate:

- improves mean throughput by 0.36 vehicles/run, about +2.91%;
- reduces mean observed travel time by 2.60 s, about -4.52%;
- slightly reduces the stop-count proxy by 0.24 vehicles/run;
- increases mean max waiting time by 1.30 s and max waiting time by 2.92 s;
- worsens waiting Gini by 0.0119;
- increases conflict pairs by 3.49 and near conflicts by 0.04 per run;
- reduces aggregate min PET by 1.25 s and mean PET by 0.52 s.

## By Demand Level

| Volume | Method | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Waiting Gini ↓ | Conflict pairs ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low | `fcfs` | 15 | 11.67 | 45.27 | 17.33 | 0.6698 | 19.00 | 0.07 | 12.70 | 40.18 |
| low | selected `prediction_coalition` | 15 | 13.80 | 40.72 | 15.97 | 0.6955 | 26.07 | 0.20 | 3.46 | 34.23 |
| medium | `fcfs` | 15 | 12.07 | 59.33 | 28.21 | 0.5675 | 22.93 | 0.40 | 14.51 | 46.33 |
| medium | selected `prediction_coalition` | 15 | 11.27 | 57.59 | 30.55 | 0.5734 | 23.60 | 0.40 | 17.84 | 48.13 |
| high | `fcfs` | 15 | 12.87 | 67.61 | 31.10 | 0.5609 | 28.27 | 0.53 | 13.06 | 39.53 |
| high | selected `prediction_coalition` | 15 | 12.60 | 66.10 | 34.03 | 0.5650 | 31.00 | 0.53 | 15.77 | 42.34 |

Demand-level reading:

- Low demand gives the largest efficiency gain, but PET and conflict-pair metrics deteriorate.
- Medium demand preserves the travel-time gain and improves PET, but loses throughput.
- High demand preserves travel-time and PET improvements, but not throughput or fairness.

## By CAV Penetration

| Penetration | Method | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Waiting Gini ↓ | Conflict pairs ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.2 | `fcfs` | 15 | 19.00 | 47.85 | 19.81 | 0.6717 | 45.33 | 0.87 | 8.98 | 33.94 |
| 0.2 | selected `prediction_coalition` | 15 | 18.93 | 46.20 | 20.97 | 0.6707 | 46.53 | 0.87 | 9.23 | 34.71 |
| 0.5 | `fcfs` | 15 | 9.80 | 62.22 | 28.16 | 0.5648 | 13.80 | 0.13 | 20.05 | 46.94 |
| 0.5 | selected `prediction_coalition` | 15 | 10.93 | 58.74 | 30.24 | 0.5861 | 19.87 | 0.13 | 16.72 | 45.79 |
| 0.8 | `fcfs` | 15 | 7.80 | 62.13 | 28.68 | 0.5616 | 11.07 | 0.00 | 11.61 | 45.21 |
| 0.8 | selected `prediction_coalition` | 15 | 7.80 | 59.48 | 29.34 | 0.5771 | 14.27 | 0.13 | 10.70 | 44.15 |

Penetration-level reading:

- Travel time improves at all tested penetration levels.
- Throughput improves mainly at 50% CAV penetration; it is flat at 80% and slightly worse at 20%.
- Safety metrics are cleanest at 20% penetration, mixed at 50%, and weaker at 80%.
- Waiting Gini becomes worse at 50% and 80% penetration.

## Pairwise Case Check

The paired comparison matches each seed, demand, and penetration setting between `fcfs` and the selected candidate.

| Metric | Preferred direction | Wins | Ties | Losses | Valid pairs | Mean delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Throughput | higher | 14 | 14 | 17 | 45 | +0.36 |
| Mean travel time | lower | 34 | 0 | 11 | 45 | -2.60 s |
| Mean max wait | lower | 9 | 0 | 36 | 45 | +1.30 s |
| Max wait | lower | 7 | 21 | 17 | 45 | +2.92 s |
| Stop proxy | lower | 10 | 28 | 7 | 45 | -0.24 |
| Waiting Gini | lower | 10 | 0 | 35 | 45 | +0.0119 |
| Conflict pairs | lower | 6 | 25 | 14 | 45 | +3.49 |
| Near conflicts | lower | 1 | 42 | 2 | 45 | +0.04 |
| Min PET | higher | 14 | 9 | 20 | 43 | -0.96 s |
| Mean PET | higher | 21 | 4 | 18 | 43 | -0.89 s |
| Min entry gap | higher | 15 | 13 | 15 | 43 | -1.17 s |

Some PET deltas have 43 valid pairs rather than 45 because PET can be absent when a run has no computable conflicting entry pair. Missing PET values are excluded rather than filled.

## Interpretation

The selected J1 candidate remains useful, but it is not a final paper-ready default.

Supported by this re-screening:

- The coalition mechanism has a repeatable travel-time benefit across the full E2 workload.
- The gain is not just an artifact of the medium/high, 50% CAV subset used in J1.
- The mechanism can increase throughput on average, but the pairwise throughput result is mixed.

Not supported yet:

- A clean safety superiority claim over FCFS.
- A fairness improvement claim.
- A final confirmatory 300 s run using this exact candidate without additional safety tuning.

The strongest wording currently justified is:

```text
The selected coalition setting reduces mean observed travel time in the T-junction mixed-traffic prototype, while exposing a safety/fairness tradeoff that requires an additional safety-constrained candidate screen before confirmatory runs.
```

## Next Experiment Decision

Do not start the 300 s, 10-seed confirmatory run with this exact candidate yet.

Instead, run a compact safety-constrained re-screening on the remote server. The next screen should reuse the same FCFS reference from this report and test coalition-only variants that reduce release aggressiveness:

```text
candidate S1: max_release_count=2, safe_arrival_gap_s=0.8, fairness_weight=0.3
candidate S2: max_release_count=2, safe_arrival_gap_s=1.2, fairness_weight=0.3
candidate S3: max_release_count=2, safe_arrival_gap_s=1.2, fairness_weight=0.15
candidate S4: max_release_count=3, safe_arrival_gap_s=0.8, fairness_weight=0.5
```

Run each over:

```text
seeds = 1..5
volumes = low, medium, high
penetrations = 0.2, 0.5, 0.8
duration = 120 s
method = prediction_coalition
```

This costs 4 x 45 = 180 additional coalition runs and avoids rerunning FCFS. A candidate should advance to confirmatory 300 s runs only if it keeps the travel-time gain while not worsening near conflicts, PET, and waiting Gini relative to the FCFS reference in this report.

No final paper superiority claim is made by this report.
