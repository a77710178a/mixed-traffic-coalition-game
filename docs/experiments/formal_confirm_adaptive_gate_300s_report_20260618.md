# Adaptive Gate 300 s Confirmatory Report

Date: 2026-06-18

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

This report records the first 10-seed confirmatory run for the geometry-aware adaptive release gate. The acceptance rule was fixed before this run in `docs/experiments/adaptive_confirmatory_acceptance_rule_20260618.md`.

## Candidate

```text
max_release_count = 2
adaptive_release_enabled = true
adaptive_max_release_count = 3
safe_arrival_gap_s = 1.2
adaptive_min_conflict_arrival_gap_s = 2.4
adaptive_max_occupancy = 0
fairness_weight = 0.0
cav_waiting_tiebreaker_weight = 0.1
```

The gate keeps the conservative two-vehicle base release set and conditionally adds one extra low-risk CAV when route-conflict geometry, projected conflict-arrival gap, and conflict-zone occupancy allow it.

## Remote Execution

Code snapshot:

```text
5994ea1
```

Remote working directories:

```text
/public/home/xiaohei_0/hx/my_paper01_confirm_adaptive_seed1_5_5994ea1
/public/home/xiaohei_0/hx/my_paper01_confirm_adaptive_seed6_10_5994ea1
```

The workload was split into two shards:

```bash
/public/home/xiaohei_0/conda38/bin/conda run -n sumoenv python sim/prototype/src/run_closed_loop_batch.py \
  --config sim/prototype/config/t_junction_scenario.json \
  --seeds 1,2,3,4,5 \
  --volumes medium,high \
  --penetrations 0.5,0.8 \
  --methods fcfs,prediction_coalition \
  --duration 300 \
  --max-release-count 2 \
  --adaptive-release-enabled \
  --adaptive-max-release-count 3 \
  --safe-arrival-gap-s 1.2 \
  --adaptive-min-conflict-arrival-gap-s 2.4 \
  --adaptive-max-occupancy 0 \
  --fairness-weight 0.0 \
  --cav-waiting-tiebreaker-weight 0.1 \
  --output-name confirm_adaptive_gate_cgap24_seed1_5_mh_pen50_80_d300
```

```bash
/public/home/xiaohei_0/conda38/bin/conda run -n sumoenv python sim/prototype/src/run_closed_loop_batch.py \
  --config sim/prototype/config/t_junction_scenario.json \
  --seeds 6,7,8,9,10 \
  --volumes medium,high \
  --penetrations 0.5,0.8 \
  --methods fcfs,prediction_coalition \
  --duration 300 \
  --max-release-count 2 \
  --adaptive-release-enabled \
  --adaptive-max-release-count 3 \
  --safe-arrival-gap-s 1.2 \
  --adaptive-min-conflict-arrival-gap-s 2.4 \
  --adaptive-max-occupancy 0 \
  --fairness-weight 0.0 \
  --cav-waiting-tiebreaker-weight 0.1 \
  --output-name confirm_adaptive_gate_cgap24_seed6_10_mh_pen50_80_d300
```

Generated artifacts copied back for analysis:

- `sim/prototype/reports/confirm_adaptive_gate_cgap24_seed1_5_mh_pen50_80_d300/closed_loop_batch_summary.json`
- `sim/prototype/reports/confirm_adaptive_gate_cgap24_seed1_5_mh_pen50_80_d300/closed_loop_batch_aggregate.csv`
- `sim/prototype/reports/confirm_adaptive_gate_cgap24_seed1_5_mh_pen50_80_d300/closed_loop_batch_runs.csv`
- `sim/prototype/reports/confirm_adaptive_gate_cgap24_seed6_10_mh_pen50_80_d300/closed_loop_batch_summary.json`
- `sim/prototype/reports/confirm_adaptive_gate_cgap24_seed6_10_mh_pen50_80_d300/closed_loop_batch_aggregate.csv`
- `sim/prototype/reports/confirm_adaptive_gate_cgap24_seed6_10_mh_pen50_80_d300/closed_loop_batch_runs.csv`

Generated outputs remain ignored by Git; this report records verified values only.

## Protocol

| Setting | Value |
| --- | --- |
| Seeds | 1 to 10 |
| Volumes | medium, high |
| CAV penetration | 0.5, 0.8 |
| Methods | `fcfs`, adaptive `prediction_coalition` |
| Duration | 300 s |
| Runs | 80 |

## Aggregate Result

| Method | Runs | Throughput up | Mean travel time down | Mean max wait down | Max wait down | Waiting Gini down | Conflict pairs down | Near conflicts down | Min PET up | Mean PET up | Min entry gap up |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fcfs` | 40 | 31.98 | 159.35 | 88.17 | 267.15 | 0.6354 | 114.10 | 0.53 | 4.01 | 90.18 | 5.79 |
| Adaptive gate | 40 | 31.45 | 157.87 | 87.74 | 269.80 | 0.6365 | 117.90 | 0.48 | 4.23 | 92.63 | 5.71 |

Positive deltas are better only for throughput, PET, and entry gap. Negative deltas are better for travel time, waiting, Gini, and conflicts.

| Metric | Adaptive - FCFS | Reading |
| --- | ---: | --- |
| Throughput | -0.53 vehicles/run | lower than FCFS |
| Mean observed travel time | -1.48 s | better |
| Mean max waiting time | -0.42 s | slightly better |
| Max waiting time | +2.65 s | worse |
| Waiting Gini | +0.0011 | slightly worse |
| Conflict-pair count | +3.80 | worse |
| Near-conflict count | -0.05 | slightly better |
| Min PET | +0.22 s | better in aggregate |
| Mean PET | +2.45 s | better |
| Min entry gap | -0.09 s | slightly worse |

## Acceptance Check

The acceptance rule was defined before this run. The candidate passes all aggregate criteria.

| Criterion | Required value | Observed value | Status |
| --- | --- | ---: | --- |
| Minimum PET | adaptive `min_pet_s >= 3.0 s` | 4.23 s | pass |
| Near conflicts | adaptive <= FCFS | 0.48 vs 0.53 | pass |
| Mean PET | adaptive > FCFS | 92.63 vs 90.18 s | pass |
| Mean travel time | adaptive < FCFS | 157.87 vs 159.35 s | pass |
| Throughput | adaptive >= S3/W0 throughput | 31.45 vs 30.25 | pass |

This promotes the adaptive gate to the current main method candidate for the prototype evidence package. It does not support a throughput-superiority claim against FCFS, because aggregate throughput remains 0.53 vehicles/run lower than FCFS.

## Pairwise Check vs FCFS

Each pair matches seed, demand level, and CAV penetration. Mean delta is adaptive minus FCFS.

| Metric | Preferred direction | Wins | Ties | Losses | Mean delta |
| --- | --- | ---: | ---: | ---: | ---: |
| Throughput | higher | 7 | 14 | 19 | -0.525 |
| Mean travel time | lower | 25 | 0 | 15 | -1.483 s |
| Mean max wait | lower | 14 | 0 | 26 | -0.425 s |
| Max wait | lower | 5 | 12 | 23 | +2.648 s |
| Waiting Gini | lower | 18 | 0 | 22 | +0.001 |
| Conflict pairs | lower | 4 | 23 | 13 | +3.800 |
| Near conflicts | lower | 3 | 36 | 1 | -0.050 |
| Min PET | higher | 12 | 20 | 8 | +0.220 s |
| Mean PET | higher | 31 | 0 | 9 | +2.452 s |
| Min entry gap | higher | 9 | 20 | 11 | -0.085 s |

## By Workload Setting

| Volume | Penetration | Metric | FCFS | Adaptive | Delta |
| --- | ---: | --- | ---: | ---: | ---: |
| high | 0.5 | Throughput | 32.80 | 32.70 | -0.10 |
| high | 0.5 | Mean travel time | 162.95 | 160.65 | -2.30 s |
| high | 0.5 | Near conflicts | 0.60 | 0.60 | 0.00 |
| high | 0.5 | Min PET | 3.35 | 3.17 | -0.18 s |
| high | 0.5 | Mean PET | 84.63 | 85.11 | +0.48 s |
| high | 0.8 | Throughput | 31.10 | 30.50 | -0.60 |
| high | 0.8 | Mean travel time | 166.22 | 166.01 | -0.21 s |
| high | 0.8 | Near conflicts | 0.20 | 0.20 | 0.00 |
| high | 0.8 | Min PET | 5.24 | 6.26 | +1.02 s |
| high | 0.8 | Mean PET | 94.50 | 99.89 | +5.39 s |
| medium | 0.5 | Throughput | 33.90 | 33.50 | -0.40 |
| medium | 0.5 | Mean travel time | 150.68 | 147.46 | -3.22 s |
| medium | 0.5 | Near conflicts | 1.00 | 0.80 | -0.20 |
| medium | 0.5 | Min PET | 3.46 | 3.65 | +0.19 s |
| medium | 0.5 | Mean PET | 88.70 | 89.72 | +1.02 s |
| medium | 0.8 | Throughput | 30.10 | 29.10 | -1.00 |
| medium | 0.8 | Mean travel time | 157.56 | 157.36 | -0.20 s |
| medium | 0.8 | Near conflicts | 0.30 | 0.30 | 0.00 |
| medium | 0.8 | Min PET | 4.00 | 3.85 | -0.15 s |
| medium | 0.8 | Mean PET | 92.89 | 95.81 | +2.92 s |

The strongest travel-time benefit appears at medium demand and 50% CAV penetration. The weakest throughput result appears at medium demand and 80% CAV penetration.

## Worst Min-PET Runs

The acceptance rule uses aggregate `min_pet_s_mean`, but the worst per-run PET values still matter for safety interpretation.

| Seed | Volume | Penetration | Adaptive min PET | FCFS min PET | Adaptive near conflicts | FCFS near conflicts | Adaptive travel time | FCFS travel time | Adaptive throughput | FCFS throughput |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | medium | 0.5 | 1.00 | 1.10 | 3 | 4 | 138.09 | 144.69 | 38 | 39 |
| 4 | medium | 0.8 | 1.00 | 1.10 | 1 | 2 | 156.34 | 154.55 | 32 | 32 |
| 7 | medium | 0.5 | 1.00 | 0.90 | 5 | 5 | 147.83 | 147.47 | 32 | 34 |
| 4 | high | 0.8 | 1.10 | 1.00 | 2 | 2 | 160.25 | 155.73 | 35 | 35 |
| 7 | high | 0.5 | 1.10 | 1.10 | 4 | 4 | 152.29 | 156.00 | 36 | 36 |
| 5 | medium | 0.8 | 1.10 | 1.20 | 2 | 1 | 163.60 | 156.50 | 27 | 30 |
| 3 | high | 0.5 | 1.20 | 1.20 | 2 | 2 | 158.41 | 163.84 | 29 | 30 |
| 9 | medium | 0.5 | 1.60 | 1.40 | 0 | 1 | 153.21 | 154.83 | 32 | 35 |

Across all 40 matched settings, the global minimum per-run `min_pet_s` is 1.00 s for adaptive and 0.90 s for FCFS. Therefore, this result should be framed as an aggregate safety and efficiency improvement under the predefined acceptance rule, not as a guarantee that every individual run has large PET margin.

## Interpretation

The 10-seed confirmatory run supports the adaptive release gate as the current main prototype candidate.

What is supported:

- The predefined aggregate acceptance rule passes.
- Mean observed travel time improves by 1.48 s/run against FCFS.
- Mean PET improves by 2.45 s, and aggregate min PET improves by 0.22 s.
- Near-conflict count decreases slightly.
- The adaptive gate recovers throughput relative to the conservative S3/W0 variants.

What is not supported:

- Throughput superiority over FCFS.
- Waiting-fairness superiority, because waiting Gini is slightly worse.
- Conflict-pair superiority, because conflict-pair count increases.
- A hard per-run PET guarantee, because several individual runs still have `min_pet_s` near 1.0 s.

## Next Decision

Use this adaptive gate as the main method candidate for the next paper-prototype stage.

The next experiments should not keep tuning this candidate blindly. Instead, they should prepare the paper evidence package around this accepted setting:

- compare against FCFS, prediction-FCFS, S3, and W0 in a clean main table;
- add robustness across more demand levels and CAV penetrations;
- add a failure-case analysis for low-PET runs;
- optionally test an extra projected-PET guard as an appendix safety refinement, without replacing the accepted main candidate unless it preserves the current travel-time benefit.

No final real-world safety claim is made by this report.
