# Safety-Constrained Candidate Screen Report

Date: 2026-06-18

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

This report follows the selected-candidate re-screening report. The R1 selected candidate improved travel time but did not give a clean safety/fairness result, so this screen tests less aggressive or more regularized coalition variants before any 300 s confirmatory run.

## Remote Execution

All four candidates were executed on the remote server in independent working directories to avoid concurrent writes to the same SUMO `routes/`, `logs/`, and `reports/` paths.

Deployed code snapshot:

```text
9a74097
```

Remote work directories:

- `/public/home/xiaohei_0/hx/my_paper01_safety_s1`
- `/public/home/xiaohei_0/hx/my_paper01_safety_s2`
- `/public/home/xiaohei_0/hx/my_paper01_safety_s3`
- `/public/home/xiaohei_0/hx/my_paper01_safety_s4`

## Protocol

| Setting | Value |
| --- | --- |
| Seeds | 1, 2, 3, 4, 5 |
| Volumes | low, medium, high |
| CAV penetration | 0.2, 0.5, 0.8 |
| Method | `prediction_coalition` |
| Duration | 120 s |
| Runs per candidate | 45 |
| New coalition runs | 180 |

The FCFS reference is reused from the completed R1 re-screening:

```text
formal_rescreen_selected_mr3_gap08_fw03_seed1_5_lmh_pen20_50_80_d120
```

## Candidate Set

| Candidate | Max release | Safe gap | Fairness weight | Intent |
| --- | ---: | ---: | ---: | --- |
| R1 selected | 3 | 0.8 | 0.3 | Efficiency-oriented selected candidate from J1 |
| S1 | 2 | 0.8 | 0.3 | Reduce release-set size while keeping R1 gap/weight |
| S2 | 2 | 1.2 | 0.3 | Conservative release size and higher gap |
| S3 | 2 | 1.2 | 0.15 | Conservative release size/gap with lower fairness regularization |
| S4 | 3 | 0.8 | 0.5 | Keep release size but increase regularization |

## Aggregate Comparison

| Candidate | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Stop proxy ↓ | Waiting Gini ↓ | Conflict pairs ↓ | Near conflicts ↓ | Min PET ↑ | Mean PET ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS reference | 45 | 12.20 | 57.40 | 25.55 | 29.49 | 0.5994 | 23.40 | 0.33 | 13.40 | 41.92 |
| R1 selected | 45 | 12.56 | 54.80 | 26.85 | 29.24 | 0.6113 | 26.89 | 0.38 | 12.15 | 41.39 |
| S1 | 45 | 11.98 | 56.38 | 26.51 | 29.11 | 0.6099 | 25.27 | 0.40 | 12.25 | 42.31 |
| S2 | 45 | 11.53 | 56.92 | 27.32 | 29.29 | 0.6027 | 24.73 | 0.36 | 13.73 | 43.37 |
| S3 | 45 | 12.04 | 56.26 | 26.66 | 29.24 | 0.6048 | 25.91 | 0.36 | 13.48 | 42.95 |
| S4 | 45 | 12.47 | 54.86 | 26.73 | 29.07 | 0.6161 | 26.33 | 0.42 | 11.85 | 41.35 |

## Delta Against FCFS

Positive throughput and PET deltas are better. Negative travel-time, waiting, Gini, conflict, and near-conflict deltas are better.

| Candidate | Throughput | Mean travel time | Mean max wait | Waiting Gini | Conflict pairs | Near conflicts | Min PET | Mean PET |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R1 selected | +0.36 | -2.60 | +1.30 | +0.0119 | +3.49 | +0.04 | -1.25 | -0.52 |
| S1 | -0.22 | -1.02 | +0.96 | +0.0105 | +1.87 | +0.07 | -1.14 | +0.40 |
| S2 | -0.67 | -0.48 | +1.77 | +0.0033 | +1.33 | +0.02 | +0.33 | +1.45 |
| S3 | -0.16 | -1.14 | +1.12 | +0.0054 | +2.51 | +0.02 | +0.08 | +1.04 |
| S4 | +0.27 | -2.54 | +1.18 | +0.0167 | +2.93 | +0.09 | -1.55 | -0.57 |

## Pairwise Wins Against FCFS

Each pair matches seed, demand level, and CAV penetration.

| Candidate | Throughput wins | Travel-time wins | Gini wins | Near-conflict wins | Min-PET wins | Mean-PET wins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| R1 selected | 14/45 | 34/45 | 10/45 | 1/45 | 14/43 | 21/43 |
| S1 | 9/45 | 25/45 | 14/45 | 0/45 | 12/43 | 21/43 |
| S2 | 6/45 | 25/45 | 18/45 | 1/45 | 17/43 | 23/43 |
| S3 | 8/45 | 30/45 | 15/45 | 1/45 | 18/43 | 20/43 |
| S4 | 14/45 | 31/45 | 14/45 | 1/45 | 14/43 | 21/43 |

PET pairs have 43 valid comparisons because two matched cases have no computable PET on at least one side.

## By Demand Level

| Candidate | Low throughput | Low travel time | Low min PET | Medium throughput | Medium travel time | Medium min PET | High throughput | High travel time | High min PET |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS reference | 11.67 | 45.27 | 12.70 | 12.07 | 59.33 | 14.51 | 12.87 | 67.61 | 13.06 |
| R1 selected | 13.80 | 40.72 | 3.46 | 11.27 | 57.59 | 17.84 | 12.60 | 66.10 | 15.77 |
| S1 | 13.07 | 42.74 | 8.86 | 10.73 | 59.12 | 15.88 | 12.13 | 67.29 | 12.26 |
| S2 | 11.93 | 43.49 | 9.43 | 10.60 | 59.54 | 19.84 | 12.07 | 67.74 | 12.24 |
| S3 | 12.93 | 42.94 | 8.91 | 10.93 | 58.69 | 19.56 | 12.27 | 67.15 | 12.30 |
| S4 | 13.80 | 40.48 | 3.25 | 11.00 | 57.77 | 17.37 | 12.60 | 66.34 | 15.54 |

## Interpretation

R1 selected and S4 are efficiency-oriented but still unsafe as final defaults:

- They give the strongest aggregate travel-time reductions.
- They keep or improve throughput relative to FCFS.
- They reduce aggregate min PET and mean PET relative to FCFS.
- S4's higher fairness weight does not fix fairness; it has the worst aggregate waiting Gini in this screen.

S1 reduces release-set size but does not recover the safety profile enough:

- It improves mean travel time relative to FCFS.
- It loses throughput and still worsens near-conflict count and min PET.
- It is not a compelling confirmatory candidate.

S2 is the most conservative safety candidate:

- It is the closest to FCFS on waiting Gini and conflict pairs among tested coalition variants.
- It improves min PET and mean PET over FCFS.
- It has the weakest efficiency result and loses 0.67 vehicles/run in throughput.

S3 is the most balanced candidate:

- It improves mean travel time by 1.14 s relative to FCFS.
- It nearly preserves throughput, with a small -0.16 vehicles/run delta.
- It improves min PET and mean PET relative to FCFS.
- It still slightly worsens waiting Gini, conflict pairs, and near conflicts, so it is not a safety-superiority result yet.

## Current Recommendation

Promote S3 as the current balanced confirmatory candidate:

```text
max_release_count = 2
safe_arrival_gap_s = 1.2
fairness_weight = 0.15
```

Keep S2 as the conservative backup:

```text
max_release_count = 2
safe_arrival_gap_s = 1.2
fairness_weight = 0.3
```

Do not use R1 selected or S4 as the main confirmatory default unless the paper chooses to emphasize efficiency with an explicit safety tradeoff.

## Next Step

Before a full 300 s, 10-seed confirmatory experiment, run a smaller 300 s pilot on the remote server:

```text
methods = fcfs, S3
seeds = 1,2,3
volumes = medium, high
penetrations = 0.5, 0.8
duration = 300 s
```

This pilot costs 3 x 2 x 2 x 2 = 24 runs. Advance to the full confirmatory experiment only if S3 preserves the travel-time/PET balance under longer simulation.

No final paper superiority claim is made by this report.
