# Adaptive Release Gate 300 s Pilot Report

Date: 2026-06-18

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

This pilot tests whether a geometry-aware adaptive release gate can recover throughput/travel-time performance after the S3 and CAV waiting tie-breaker pilots showed that static release eligibility was too conservative.

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

The gate keeps the S3 two-vehicle base release set and conditionally adds one extra low-risk CAV when route-conflict geometry, projected arrival gap, and conflict-zone occupancy allow it.

## Remote Execution

Code snapshot:

```text
f981c08
```

Remote working directory:

```text
/public/home/xiaohei_0/hx/my_paper01_adaptive_gate_f981c08
```

Command:

```bash
/public/home/xiaohei_0/conda38/bin/conda run -n sumoenv python sim/prototype/src/run_closed_loop_batch.py \
  --config sim/prototype/config/t_junction_scenario.json \
  --seeds 1,2,3 \
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
  --output-name formal_pilot_adaptive_gate_mr2_amr3_gap12_cgap24_occ0_fw0_tb01_seed1_3_mh_pen50_80_d300
```

Generated artifacts copied back for analysis:

- `sim/prototype/reports/formal_pilot_adaptive_gate_mr2_amr3_gap12_cgap24_occ0_fw0_tb01_seed1_3_mh_pen50_80_d300/closed_loop_batch_summary.json`
- `sim/prototype/reports/formal_pilot_adaptive_gate_mr2_amr3_gap12_cgap24_occ0_fw0_tb01_seed1_3_mh_pen50_80_d300/closed_loop_batch_aggregate.csv`
- `sim/prototype/reports/formal_pilot_adaptive_gate_mr2_amr3_gap12_cgap24_occ0_fw0_tb01_seed1_3_mh_pen50_80_d300/closed_loop_batch_runs.csv`

Generated outputs remain ignored by Git; this report records verified values only.

## Protocol

| Setting | Value |
| --- | --- |
| Seeds | 1, 2, 3 |
| Volumes | medium, high |
| CAV penetration | 0.5, 0.8 |
| Methods | `fcfs`, adaptive `prediction_coalition` |
| Duration | 300 s |
| Runs | 24 |

## Aggregate Result

| Candidate | Runs | Throughput up | Mean travel time down | Mean max wait down | Max wait down | Waiting Gini down | Conflict pairs down | Near conflicts down | Min PET up | Mean PET up |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 12 | 31.42 | 158.33 | 91.01 | 269.04 | 0.6279 | 131.00 | 0.50 | 3.34 | 89.77 |
| S3 `fw=0.15,tb=0.0` | 12 | 30.25 | 158.62 | 92.75 | 273.15 | 0.6269 | 136.25 | 0.42 | 3.41 | 92.41 |
| W0 `fw=0.0,tb=0.1` | 12 | 30.25 | 156.75 | 92.79 | 271.62 | 0.6266 | 136.25 | 0.42 | 3.42 | 92.61 |
| Adaptive gate | 12 | 30.33 | 156.44 | 92.48 | 273.93 | 0.6266 | 136.25 | 0.42 | 3.12 | 93.31 |

## Delta vs FCFS

Positive deltas are better only for throughput and PET. Negative deltas are better for travel time, waiting, conflicts, and Gini.

| Candidate | Throughput delta | Travel delta | Mean max wait delta | Max wait delta | Gini delta | Conflict pair delta | Near conflict delta | Min PET delta | Mean PET delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| S3 `fw=0.15,tb=0.0` | -1.17 | +0.28 | +1.74 | +4.11 | -0.0010 | +5.25 | -0.08 | +0.07 | +2.64 |
| W0 `fw=0.0,tb=0.1` | -1.17 | -1.58 | +1.78 | +2.58 | -0.0013 | +5.25 | -0.08 | +0.08 | +2.84 |
| Adaptive gate | -1.08 | -1.89 | +1.47 | +4.89 | -0.0013 | +5.25 | -0.08 | -0.22 | +3.55 |

## Delta vs W0

| Throughput delta | Travel delta | Mean max wait delta | Max wait delta | Gini delta | Conflict pair delta | Near conflict delta | Min PET delta | Mean PET delta |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| +0.08 | -0.31 | -0.31 | +2.31 | +0.0000 | +0.00 | +0.00 | -0.30 | +0.71 |

## Pairwise Check vs FCFS

Each pair matches seed, demand, and CAV penetration.

| Candidate | Metric | Preferred direction | Wins | Ties | Losses | Mean delta |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Adaptive gate | Throughput | higher | 1 | 3 | 8 | -1.083 |
| Adaptive gate | Mean travel time | lower | 7 | 0 | 5 | -1.893 s |
| Adaptive gate | Mean max wait | lower | 3 | 0 | 9 | +1.467 s |
| Adaptive gate | Max wait | lower | 1 | 4 | 7 | +4.892 s |
| Adaptive gate | Waiting Gini | lower | 7 | 0 | 5 | -0.001 |
| Adaptive gate | Conflict pairs | lower | 2 | 7 | 3 | +5.250 |
| Adaptive gate | Near conflicts | lower | 1 | 11 | 0 | -0.083 |
| Adaptive gate | Min PET | higher | 1 | 8 | 3 | -0.225 s |
| Adaptive gate | Mean PET | higher | 9 | 0 | 3 | +3.545 s |

## Worst Min-PET Runs

| Seed | Volume | Penetration | Adaptive min PET | FCFS min PET | Adaptive throughput | FCFS throughput |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | medium | 0.5 | 1.00 | 1.10 | 38 | 39 |
| 3 | high | 0.5 | 1.20 | 1.20 | 29 | 30 |
| 1 | high | 0.5 | 1.80 | 1.70 | 38 | 38 |
| 1 | high | 0.8 | 2.20 | 2.20 | 30 | 32 |
| 1 | medium | 0.8 | 2.30 | 4.00 | 31 | 32 |

## Interpretation

The adaptive release gate is a useful mechanism direction, but this exact parameterization is not ready as the final method.

What improves:

- Adaptive gate improves aggregate throughput slightly over S3/W0: 30.33 vs 30.25 vehicles/run.
- It gives the best mean observed travel time in this pilot: 156.44 s.
- It preserves the S3/W0 near-conflict count of 0.42 and improves mean PET to 93.31 s.
- It improves pairwise mean travel time in 7 of 12 matched cases against FCFS.

What remains unsafe or unclear:

- Min PET decreases to 3.12 s, below FCFS, S3, and W0.
- Max waiting worsens relative to W0 and FCFS.
- Conflict-pair count is unchanged from S3/W0 and still above FCFS.
- Throughput recovery is small, not enough to justify a 10-seed confirmatory run.

The min-PET regression suggests the extra-release gate is still too permissive for a few local cases. The mechanism is promising because it improves travel time and mean PET, but it needs a sharper safety guard before being promoted.

## Next Decision

Do not run a full 300 s, 10-seed confirmatory experiment yet.

The next method step should test a stricter adaptive gate:

```text
keep base max_release_count = 2
keep adaptive_max_release_count = 3
increase adaptive_min_conflict_arrival_gap_s from 2.4 to 3.6 or 4.0
or add an explicit extra-release min projected PET guard
keep adaptive_max_occupancy = 0
keep fairness_weight = 0.0
keep cav_waiting_tiebreaker_weight = 0.1
```

Recommended next pilot:

```text
adaptive_min_conflict_arrival_gap_s in {3.6, 4.0}
same 300 s protocol
compare against FCFS, S3, W0, and the current adaptive gate
```

No final paper superiority claim is made by this report.
