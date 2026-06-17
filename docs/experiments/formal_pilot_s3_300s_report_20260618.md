# S3 300 s Pilot Report

Date: 2026-06-18

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

This pilot tests whether the safety-balanced S3 candidate from the 120 s screen remains promising under longer 300 s simulations.

## Candidate

```text
max_release_count = 2
safe_arrival_gap_s = 1.2
fairness_weight = 0.15
```

## Remote Execution

Remote working directory:

```text
/public/home/xiaohei_0/hx/my_paper01_pilot_s3_300s
```

Deployed code snapshot:

```text
9a74097
```

Command:

```bash
/public/home/xiaohei_0/conda38/bin/conda run -n sumoenv python src/run_closed_loop_batch.py \
  --config config/t_junction_scenario.json \
  --seeds 1,2,3 \
  --volumes medium,high \
  --penetrations 0.5,0.8 \
  --methods fcfs,prediction_coalition \
  --duration 300 \
  --control-radius-m 45 \
  --fairness-weight 0.15 \
  --max-release-count 2 \
  --safe-arrival-gap-s 1.2 \
  --near-conflict-pet-s 1.5 \
  --output-name formal_pilot_s3_mr2_gap12_fw015_seed1_3_mh_pen50_80_d300
```

Generated remote artifacts:

- `reports/formal_pilot_s3_mr2_gap12_fw015_seed1_3_mh_pen50_80_d300/closed_loop_batch_summary.json`
- `reports/formal_pilot_s3_mr2_gap12_fw015_seed1_3_mh_pen50_80_d300/closed_loop_batch_aggregate.csv`
- `reports/formal_pilot_s3_mr2_gap12_fw015_seed1_3_mh_pen50_80_d300/closed_loop_batch_runs.csv`

The summary artifacts were copied back for analysis. Generated outputs remain ignored by Git; this document records verified values only.

## Protocol

| Setting | Value |
| --- | --- |
| Seeds | 1, 2, 3 |
| Volumes | medium, high |
| CAV penetration | 0.5, 0.8 |
| Methods | `fcfs`, S3 `prediction_coalition` |
| Duration | 300 s |
| Runs | 24 |

## Aggregate Result

| Method | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Max wait ↓ | Stop proxy ↓ | Waiting Gini ↓ | Conflict pairs ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fcfs` | 12 | 31.42 | 158.33 | 91.01 | 269.04 | 33.42 | 0.6279 | 131.00 | 0.50 | 3.34 | 89.77 |
| S3 `prediction_coalition` | 12 | 30.25 | 158.62 | 92.75 | 273.15 | 33.08 | 0.6269 | 136.25 | 0.42 | 3.41 | 92.41 |

Relative to `fcfs`, S3:

- decreases throughput by 1.17 vehicles/run;
- increases mean observed travel time by 0.28 s;
- increases mean max waiting time by 1.74 s and max waiting time by 4.11 s;
- slightly improves stop proxy by 0.33 vehicles/run;
- slightly improves waiting Gini by 0.0010;
- increases conflict-pair count by 5.25;
- reduces near-conflict count by 0.08 per run;
- slightly improves min PET by 0.07 s and mean PET by 2.64 s.

## By Demand Level

| Volume | Method | Runs | Throughput ↑ | Mean travel time ↓ | Waiting Gini ↓ | Conflict pairs ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| medium | `fcfs` | 6 | 31.50 | 153.19 | 0.6312 | 127.00 | 0.67 | 3.47 | 92.34 |
| medium | S3 | 6 | 30.33 | 152.92 | 0.6283 | 137.83 | 0.50 | 3.30 | 96.59 |
| high | `fcfs` | 6 | 31.33 | 163.48 | 0.6246 | 135.00 | 0.33 | 3.22 | 87.20 |
| high | S3 | 6 | 30.17 | 164.32 | 0.6254 | 134.67 | 0.33 | 3.52 | 88.23 |

Demand-level reading:

- Medium demand preserves a tiny travel-time benefit and improves Gini, near-conflict count, and mean PET, but loses throughput and worsens conflict-pair count.
- High demand improves PET and slightly lowers conflict-pair count, but loses throughput and worsens mean travel time.

## By CAV Penetration

| Penetration | Method | Runs | Throughput ↑ | Mean travel time ↓ | Waiting Gini ↓ | Conflict pairs ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.5 | `fcfs` | 6 | 32.67 | 156.86 | 0.6322 | 116.67 | 1.00 | 2.43 | 87.85 |
| 0.5 | S3 | 6 | 32.17 | 156.08 | 0.6331 | 129.33 | 0.83 | 2.42 | 91.71 |
| 0.8 | `fcfs` | 6 | 30.17 | 159.81 | 0.6236 | 145.33 | 0.00 | 4.25 | 91.69 |
| 0.8 | S3 | 6 | 28.33 | 161.16 | 0.6206 | 143.17 | 0.00 | 4.40 | 93.11 |

Penetration-level reading:

- At 50% CAV penetration, S3 improves mean travel time and near conflicts but worsens conflict-pair count and waiting Gini.
- At 80% CAV penetration, S3 improves Gini, conflict-pair count, and PET, but loses throughput and travel time.

## Pairwise Check

Each pair matches seed, demand, and penetration.

| Metric | Preferred direction | Wins | Ties | Losses | Mean delta |
| --- | --- | ---: | ---: | ---: | ---: |
| Throughput | higher | 1 | 3 | 8 | -1.17 |
| Mean travel time | lower | 6 | 0 | 6 | +0.28 s |
| Waiting Gini | lower | 6 | 0 | 6 | -0.0010 |
| Conflict pairs | lower | 2 | 7 | 3 | +5.25 |
| Near conflicts | lower | 1 | 11 | 0 | -0.08 |
| Min PET | higher | 3 | 6 | 3 | +0.07 s |
| Mean PET | higher | 8 | 0 | 4 | +2.64 s |

## Interpretation

The 300 s pilot does not support S3 as an efficiency-improving final default.

What the pilot supports:

- S3 is a safety-leaning candidate under longer simulation.
- It reduces near-conflict count and improves mean PET in this small 300 s workload.
- It slightly improves aggregate waiting Gini.

What the pilot does not support:

- A throughput improvement over FCFS.
- A robust mean-travel-time improvement over FCFS.
- A clean conflict-pair reduction.

The result changes the experiment direction: S3 should not be promoted directly to the full 300 s, 10-seed confirmatory experiment as the main method. It is better used as a conservative safety variant or appendix/ablation point.

## Next Decision

Do not run a full 300 s, 10-seed confirmatory experiment yet.

The next method step should adjust the release rule before more large runs:

```text
keep max_release_count = 2
keep safe_arrival_gap_s = 1.2
test fairness_weight = 0.0 or 0.1
add a throughput-preserving tie-breaker for long-waiting released CAVs
```

After the rule adjustment, repeat a 300 s pilot with:

```text
methods = fcfs, adjusted coalition, S3
seeds = 1,2,3
volumes = medium, high
penetrations = 0.5, 0.8
duration = 300 s
```

No final paper superiority claim is made by this report.
