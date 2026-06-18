# CAV Waiting Tie-Breaker 300 s Pilot Report

Date: 2026-06-18

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

This pilot tests whether the conservative S3 release rule can recover efficiency by adding a small CAV waiting-time tie-breaker while keeping the safer release cap and arrival-gap structure.

## Candidates

All adjusted candidates use:

```text
max_release_count = 2
safe_arrival_gap_s = 1.2
cav_waiting_tiebreaker_weight = 0.1
```

The two tested variants are:

| Candidate | Fairness weight | Purpose |
| --- | ---: | --- |
| W0 | 0.0 | Remove global fairness regularization and use only the CAV waiting tie-breaker |
| W1 | 0.1 | Retain a small global fairness term plus the CAV waiting tie-breaker |

The reference S3 candidate is:

```text
max_release_count = 2
safe_arrival_gap_s = 1.2
fairness_weight = 0.15
cav_waiting_tiebreaker_weight = 0.0
```

## Remote Execution

Code snapshot:

```text
25d7283
```

Remote working directories:

```text
/public/home/xiaohei_0/hx/my_paper01_wait_tb_fw0_25d7283
/public/home/xiaohei_0/hx/my_paper01_wait_tb_fw01_25d7283
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
  --safe-arrival-gap-s 1.2 \
  --fairness-weight 0.0 \
  --cav-waiting-tiebreaker-weight 0.1 \
  --output-name formal_pilot_adjusted_wait_tb01_fw0_seed1_3_mh_pen50_80_d300
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
  --safe-arrival-gap-s 1.2 \
  --fairness-weight 0.1 \
  --cav-waiting-tiebreaker-weight 0.1 \
  --output-name formal_pilot_adjusted_wait_tb01_fw01_seed1_3_mh_pen50_80_d300
```

Generated artifacts copied back for analysis:

- `sim/prototype/reports/formal_pilot_adjusted_wait_tb01_fw0_seed1_3_mh_pen50_80_d300/closed_loop_batch_summary.json`
- `sim/prototype/reports/formal_pilot_adjusted_wait_tb01_fw0_seed1_3_mh_pen50_80_d300/closed_loop_batch_aggregate.csv`
- `sim/prototype/reports/formal_pilot_adjusted_wait_tb01_fw0_seed1_3_mh_pen50_80_d300/closed_loop_batch_runs.csv`
- `sim/prototype/reports/formal_pilot_adjusted_wait_tb01_fw01_seed1_3_mh_pen50_80_d300/closed_loop_batch_summary.json`
- `sim/prototype/reports/formal_pilot_adjusted_wait_tb01_fw01_seed1_3_mh_pen50_80_d300/closed_loop_batch_aggregate.csv`
- `sim/prototype/reports/formal_pilot_adjusted_wait_tb01_fw01_seed1_3_mh_pen50_80_d300/closed_loop_batch_runs.csv`

Generated outputs remain ignored by Git; this report records verified values only.

## Protocol

| Setting | Value |
| --- | --- |
| Seeds | 1, 2, 3 |
| Volumes | medium, high |
| CAV penetration | 0.5, 0.8 |
| Methods | `fcfs`, adjusted `prediction_coalition` |
| Duration | 300 s |
| Runs | 48 adjusted pilot runs |

The same FCFS reference is deterministic for the matched scenario settings, so FCFS values match the S3 300 s pilot.

## Aggregate Result

| Candidate | Runs | Throughput up | Mean travel time down | Mean max wait down | Max wait down | Waiting Gini down | Conflict pairs down | Near conflicts down | Min PET up | Mean PET up |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 12 | 31.42 | 158.33 | 91.01 | 269.04 | 0.6279 | 131.00 | 0.50 | 3.34 | 89.77 |
| S3 `fw=0.15,tb=0.0` | 12 | 30.25 | 158.62 | 92.75 | 273.15 | 0.6269 | 136.25 | 0.42 | 3.41 | 92.41 |
| W0 `fw=0.0,tb=0.1` | 12 | 30.25 | 156.75 | 92.79 | 271.62 | 0.6266 | 136.25 | 0.42 | 3.42 | 92.61 |
| W1 `fw=0.1,tb=0.1` | 12 | 30.25 | 158.52 | 92.72 | 271.32 | 0.6268 | 136.25 | 0.42 | 3.41 | 92.28 |

## Delta vs FCFS

Positive deltas are better only for throughput and PET. Negative deltas are better for travel time, waiting, conflicts, and Gini.

| Candidate | Throughput delta | Travel delta | Mean max wait delta | Max wait delta | Gini delta | Conflict pair delta | Near conflict delta | Min PET delta | Mean PET delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| S3 `fw=0.15,tb=0.0` | -1.17 | +0.28 | +1.74 | +4.11 | -0.0010 | +5.25 | -0.08 | +0.07 | +2.64 |
| W0 `fw=0.0,tb=0.1` | -1.17 | -1.58 | +1.78 | +2.58 | -0.0013 | +5.25 | -0.08 | +0.08 | +2.84 |
| W1 `fw=0.1,tb=0.1` | -1.17 | +0.18 | +1.70 | +2.27 | -0.0011 | +5.25 | -0.08 | +0.07 | +2.51 |

## Delta vs S3

| Candidate | Throughput delta | Travel delta | Mean max wait delta | Max wait delta | Gini delta | Conflict pair delta | Near conflict delta | Min PET delta | Mean PET delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| W0 `fw=0.0,tb=0.1` | +0.00 | -1.87 | +0.04 | -1.52 | -0.0003 | +0.00 | +0.00 | +0.01 | +0.20 |
| W1 `fw=0.1,tb=0.1` | +0.00 | -0.10 | -0.04 | -1.83 | -0.0001 | +0.00 | +0.00 | +0.00 | -0.13 |

## By Demand Level

| Volume | Candidate | Throughput up | Mean travel time down | Gini down | Conflict pairs down | Near conflicts down | Min PET up | Mean PET up |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| medium | FCFS | 31.50 | 153.19 | 0.6312 | 127.00 | 0.67 | 3.47 | 92.34 |
| medium | S3 | 30.33 | 152.92 | 0.6283 | 137.83 | 0.50 | 3.30 | 96.59 |
| medium | W0 | 30.33 | 150.57 | 0.6277 | 137.83 | 0.50 | 3.30 | 96.83 |
| medium | W1 | 30.33 | 152.80 | 0.6284 | 137.83 | 0.50 | 3.30 | 96.55 |
| high | FCFS | 31.33 | 163.48 | 0.6246 | 135.00 | 0.33 | 3.22 | 87.20 |
| high | S3 | 30.17 | 164.32 | 0.6254 | 134.67 | 0.33 | 3.52 | 88.23 |
| high | W0 | 30.17 | 162.92 | 0.6254 | 134.67 | 0.33 | 3.53 | 88.38 |
| high | W1 | 30.17 | 164.24 | 0.6251 | 134.67 | 0.33 | 3.52 | 88.01 |

## By CAV Penetration

| Penetration | Candidate | Throughput up | Mean travel time down | Gini down | Conflict pairs down | Near conflicts down | Min PET up | Mean PET up |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.5 | FCFS | 32.67 | 156.86 | 0.6322 | 116.67 | 1.00 | 2.43 | 87.85 |
| 0.5 | S3 | 32.17 | 156.08 | 0.6331 | 129.33 | 0.83 | 2.42 | 91.71 |
| 0.5 | W0 | 32.17 | 153.64 | 0.6322 | 129.33 | 0.83 | 2.43 | 91.89 |
| 0.5 | W1 | 32.17 | 155.74 | 0.6329 | 129.33 | 0.83 | 2.42 | 91.75 |
| 0.8 | FCFS | 30.17 | 159.81 | 0.6236 | 145.33 | 0.00 | 4.25 | 91.69 |
| 0.8 | S3 | 28.33 | 161.16 | 0.6206 | 143.17 | 0.00 | 4.40 | 93.11 |
| 0.8 | W0 | 28.33 | 159.85 | 0.6209 | 143.17 | 0.00 | 4.40 | 93.33 |
| 0.8 | W1 | 28.33 | 161.30 | 0.6206 | 143.17 | 0.00 | 4.40 | 92.81 |

## Pairwise Check vs FCFS

Each pair matches seed, demand, and CAV penetration.

| Candidate | Metric | Preferred direction | Wins | Ties | Losses | Mean delta |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| W0 | Throughput | higher | 1 | 3 | 8 | -1.167 |
| W0 | Mean travel time | lower | 6 | 0 | 6 | -1.584 s |
| W0 | Waiting Gini | lower | 6 | 0 | 6 | -0.001 |
| W0 | Conflict pairs | lower | 2 | 7 | 3 | +5.250 |
| W0 | Near conflicts | lower | 1 | 11 | 0 | -0.083 |
| W0 | Min PET | higher | 2 | 8 | 2 | +0.075 s |
| W0 | Mean PET | higher | 8 | 0 | 4 | +2.839 s |
| W1 | Throughput | higher | 1 | 3 | 8 | -1.167 |
| W1 | Mean travel time | lower | 5 | 0 | 7 | +0.185 s |
| W1 | Waiting Gini | lower | 6 | 0 | 6 | -0.001 |
| W1 | Conflict pairs | lower | 2 | 7 | 3 | +5.250 |
| W1 | Near conflicts | lower | 1 | 11 | 0 | -0.083 |
| W1 | Min PET | higher | 2 | 7 | 3 | +0.067 s |
| W1 | Mean PET | higher | 8 | 0 | 4 | +2.511 s |

## Interpretation

The CAV waiting tie-breaker is partially useful but not enough for the final method.

What improves:

- W0 reduces mean observed travel time by 1.58 s relative to FCFS and by 1.87 s relative to S3.
- W0 slightly improves max waiting time, waiting Gini, min PET, and mean PET relative to S3.
- Both adjusted variants preserve the S3 near-conflict reduction and PET-leaning behavior.

What does not improve:

- Throughput remains 30.25 vehicles/run for all S3/W0/W1 variants, still 1.17 vehicles/run below FCFS.
- Conflict-pair count remains 136.25, still above FCFS.
- Mean max waiting remains worse than FCFS.
- W1 largely collapses back toward S3 on mean travel time.

The key diagnosis is that the throughput loss is not caused mainly by fairness ordering or by CAV waiting priority. It is caused by the release eligibility structure: `max_release_count=2` and the close-arrival blocking rule decide how many vehicles can enter, while the tie-breaker only changes ordering among already eligible vehicles.

## Next Decision

Do not run a 10-seed, 300 s confirmatory experiment with W0 or W1 as the final method.

Use W0 as a diagnostic stepping stone, not as the final candidate.

The next method step should move from a scalar waiting tie-breaker to an adaptive release-set gate:

```text
base release cap = 2
allow an additional low-risk CAV release only when predicted conflict exposure is low
keep HDV close-arrival protection
make the extra release conditional on route-conflict relation, projected arrival separation, and current conflict-zone occupancy
```

The next pilot should test an adaptive gate against FCFS, S3, and W0 on the same 300 s protocol before any larger confirmatory run.

No final paper superiority claim is made by this report.
