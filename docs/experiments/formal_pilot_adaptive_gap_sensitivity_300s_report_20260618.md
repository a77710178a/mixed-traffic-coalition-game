# Adaptive Gap Sensitivity 300 s Pilot Report

Date: 2026-06-18

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

This pilot tests whether making the adaptive extra-release conflict-arrival gap stricter can repair the min-PET regression observed in P3.

## Candidates

Both candidates keep the P3 adaptive release gate and only change `adaptive_min_conflict_arrival_gap_s`.

Common settings:

```text
max_release_count = 2
adaptive_release_enabled = true
adaptive_max_release_count = 3
safe_arrival_gap_s = 1.2
adaptive_max_occupancy = 0
fairness_weight = 0.0
cav_waiting_tiebreaker_weight = 0.1
```

Sensitivity values:

```text
adaptive_min_conflict_arrival_gap_s = 3.6
adaptive_min_conflict_arrival_gap_s = 4.0
```

## Remote Execution

Code snapshot:

```text
1840fae
```

Remote working directories:

```text
/public/home/xiaohei_0/hx/my_paper01_adaptive_gate_cgap36_1840fae
/public/home/xiaohei_0/hx/my_paper01_adaptive_gate_cgap40_1840fae
```

Commands:

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
  --adaptive-min-conflict-arrival-gap-s 3.6 \
  --adaptive-max-occupancy 0 \
  --fairness-weight 0.0 \
  --cav-waiting-tiebreaker-weight 0.1 \
  --output-name formal_pilot_adaptive_gate_mr2_amr3_gap12_cgap36_occ0_fw0_tb01_seed1_3_mh_pen50_80_d300
```

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
  --adaptive-min-conflict-arrival-gap-s 4.0 \
  --adaptive-max-occupancy 0 \
  --fairness-weight 0.0 \
  --cav-waiting-tiebreaker-weight 0.1 \
  --output-name formal_pilot_adaptive_gate_mr2_amr3_gap12_cgap40_occ0_fw0_tb01_seed1_3_mh_pen50_80_d300
```

Generated artifacts copied back for analysis:

- `sim/prototype/reports/formal_pilot_adaptive_gate_mr2_amr3_gap12_cgap36_occ0_fw0_tb01_seed1_3_mh_pen50_80_d300/closed_loop_batch_summary.json`
- `sim/prototype/reports/formal_pilot_adaptive_gate_mr2_amr3_gap12_cgap36_occ0_fw0_tb01_seed1_3_mh_pen50_80_d300/closed_loop_batch_aggregate.csv`
- `sim/prototype/reports/formal_pilot_adaptive_gate_mr2_amr3_gap12_cgap36_occ0_fw0_tb01_seed1_3_mh_pen50_80_d300/closed_loop_batch_runs.csv`
- `sim/prototype/reports/formal_pilot_adaptive_gate_mr2_amr3_gap12_cgap40_occ0_fw0_tb01_seed1_3_mh_pen50_80_d300/closed_loop_batch_summary.json`
- `sim/prototype/reports/formal_pilot_adaptive_gate_mr2_amr3_gap12_cgap40_occ0_fw0_tb01_seed1_3_mh_pen50_80_d300/closed_loop_batch_aggregate.csv`
- `sim/prototype/reports/formal_pilot_adaptive_gate_mr2_amr3_gap12_cgap40_occ0_fw0_tb01_seed1_3_mh_pen50_80_d300/closed_loop_batch_runs.csv`

Generated outputs remain ignored by Git; this report records verified values only.

## Protocol

| Setting | Value |
| --- | --- |
| Seeds | 1, 2, 3 |
| Volumes | medium, high |
| CAV penetration | 0.5, 0.8 |
| Methods | `fcfs`, adaptive `prediction_coalition` |
| Duration | 300 s |
| Runs | 48 |

## Aggregate Result

| Candidate | Runs | Throughput up | Mean travel time down | Mean max wait down | Max wait down | Waiting Gini down | Conflict pairs down | Near conflicts down | Min PET up | Mean PET up | Min entry gap up |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 12 | 31.42 | 158.33 | 91.01 | 269.04 | 0.6279 | 131.00 | 0.50 | 3.34 | 89.77 | 5.03 |
| S3 | 12 | 30.25 | 158.62 | 92.75 | 273.15 | 0.6269 | 136.25 | 0.42 | 3.41 | 92.41 | 5.12 |
| W0 | 12 | 30.25 | 156.75 | 92.79 | 271.62 | 0.6266 | 136.25 | 0.42 | 3.42 | 92.61 | 5.10 |
| Adaptive `cgap=2.4` | 12 | 30.33 | 156.44 | 92.48 | 273.93 | 0.6266 | 136.25 | 0.42 | 3.12 | 93.31 | 4.40 |
| Adaptive `cgap=3.6` | 12 | 30.33 | 156.62 | 92.53 | 274.01 | 0.6268 | 136.25 | 0.42 | 3.12 | 92.84 | 4.40 |
| Adaptive `cgap=4.0` | 12 | 30.33 | 156.62 | 92.53 | 274.02 | 0.6268 | 136.25 | 0.42 | 3.12 | 92.88 | 4.40 |

## Delta vs W0

| Candidate | Throughput delta | Travel delta | Mean max wait delta | Max wait delta | Min PET delta | Mean PET delta | Min entry gap delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Adaptive `cgap=2.4` | +0.08 | -0.31 | -0.31 | +2.31 | -0.30 | +0.71 | -0.70 |
| Adaptive `cgap=3.6` | +0.08 | -0.13 | -0.26 | +2.38 | -0.30 | +0.23 | -0.70 |
| Adaptive `cgap=4.0` | +0.08 | -0.13 | -0.26 | +2.39 | -0.30 | +0.27 | -0.70 |

## Worst Min-PET Runs

The worst min-PET cases are identical across the three adaptive-gap settings.

| Candidate | Seed | Volume | Penetration | Min PET | FCFS min PET | Throughput | FCFS throughput |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `cgap=2.4` | 1 | medium | 0.5 | 1.00 | 1.10 | 38 | 39 |
| `cgap=2.4` | 3 | high | 0.5 | 1.20 | 1.20 | 29 | 30 |
| `cgap=2.4` | 1 | high | 0.5 | 1.80 | 1.70 | 38 | 38 |
| `cgap=2.4` | 1 | high | 0.8 | 2.20 | 2.20 | 30 | 32 |
| `cgap=2.4` | 1 | medium | 0.8 | 2.30 | 4.00 | 31 | 32 |
| `cgap=3.6` | 1 | medium | 0.5 | 1.00 | 1.10 | 38 | 39 |
| `cgap=3.6` | 3 | high | 0.5 | 1.20 | 1.20 | 29 | 30 |
| `cgap=3.6` | 1 | high | 0.5 | 1.80 | 1.70 | 38 | 38 |
| `cgap=3.6` | 1 | high | 0.8 | 2.20 | 2.20 | 30 | 32 |
| `cgap=3.6` | 1 | medium | 0.8 | 2.30 | 4.00 | 31 | 32 |
| `cgap=4.0` | 1 | medium | 0.5 | 1.00 | 1.10 | 38 | 39 |
| `cgap=4.0` | 3 | high | 0.5 | 1.20 | 1.20 | 29 | 30 |
| `cgap=4.0` | 1 | high | 0.5 | 1.80 | 1.70 | 38 | 38 |
| `cgap=4.0` | 1 | high | 0.8 | 2.20 | 2.20 | 30 | 32 |
| `cgap=4.0` | 1 | medium | 0.8 | 2.30 | 4.00 | 31 | 32 |

## Pairwise Check vs FCFS

| Candidate | Metric | Wins | Ties | Losses | Mean delta |
| --- | --- | ---: | ---: | ---: | ---: |
| S3 | Throughput | 1 | 3 | 8 | -1.167 |
| S3 | Mean travel time | 6 | 0 | 6 | +0.283 s |
| S3 | Min PET | 2 | 7 | 3 | +0.067 s |
| S3 | Mean PET | 8 | 0 | 4 | +2.638 s |
| W0 | Throughput | 1 | 3 | 8 | -1.167 |
| W0 | Mean travel time | 6 | 0 | 6 | -1.584 s |
| W0 | Min PET | 2 | 8 | 2 | +0.075 s |
| W0 | Mean PET | 8 | 0 | 4 | +2.839 s |
| Adaptive `cgap=2.4` | Throughput | 1 | 3 | 8 | -1.083 |
| Adaptive `cgap=2.4` | Mean travel time | 7 | 0 | 5 | -1.893 s |
| Adaptive `cgap=2.4` | Min PET | 1 | 8 | 3 | -0.225 s |
| Adaptive `cgap=2.4` | Mean PET | 9 | 0 | 3 | +3.545 s |
| Adaptive `cgap=3.6` | Throughput | 1 | 3 | 8 | -1.083 |
| Adaptive `cgap=3.6` | Mean travel time | 6 | 0 | 6 | -1.712 s |
| Adaptive `cgap=3.6` | Min PET | 1 | 8 | 3 | -0.225 s |
| Adaptive `cgap=3.6` | Mean PET | 9 | 0 | 3 | +3.069 s |
| Adaptive `cgap=4.0` | Throughput | 1 | 3 | 8 | -1.083 |
| Adaptive `cgap=4.0` | Mean travel time | 6 | 0 | 6 | -1.716 s |
| Adaptive `cgap=4.0` | Min PET | 1 | 8 | 3 | -0.225 s |
| Adaptive `cgap=4.0` | Mean PET | 9 | 0 | 3 | +3.110 s |

## Interpretation

Increasing the adaptive conflict-arrival gap from 2.4 s to 3.6 s or 4.0 s does not repair the min-PET regression.

What this sensitivity test shows:

- Throughput remains 30.33 vehicles/run for all adaptive-gap settings.
- Mean travel time remains better than FCFS and W0, but worsens slightly as the gap is increased.
- Min PET remains 3.12 s for all adaptive-gap settings.
- Worst min-PET cases are identical across 2.4, 3.6, and 4.0.
- Mean PET remains above FCFS/S3/W0, but declines from the 2.4 s setting.

This means the min-PET issue is not controlled by `adaptive_min_conflict_arrival_gap_s` in this workload. The risky extra releases are likely passing the current route-conflict gate because they are non-conflicting in the static matrix, or because the relevant risk is not captured by the pairwise conflict-arrival gap alone.

## Next Decision

Do not run a full 300 s, 10-seed confirmatory experiment yet.

Do not continue tuning `adaptive_min_conflict_arrival_gap_s` alone.

The next method step should add an explicit extra-release safety guard, for example:

```text
extra release requires projected minimum PET >= 3.4 s
or extra release requires projected minimum entry gap >= 5.0 s
or extra release is disabled for cases where any current candidate is already inside the conflict zone
```

Recommended next implementation direction:

```text
add an adaptive_extra_min_arrival_gap_s guard across all already released vehicles
test values in {4.8, 5.0}
keep adaptive_min_conflict_arrival_gap_s = 2.4
keep adaptive_max_occupancy = 0
same 300 s protocol
```

No final paper superiority claim is made by this report.
