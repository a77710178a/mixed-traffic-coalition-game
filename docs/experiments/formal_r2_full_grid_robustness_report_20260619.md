# R2 Full-Grid Robustness Report

Date: 2026-06-19

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

This report records the first full-grid robustness run after the C1 adaptive-gate confirmatory experiment. It is labeled R2 because R1 already denotes the earlier selected-candidate re-screening. R2 tests whether the C1 signal generalizes beyond medium/high demand and 50%/80% CAV penetration.

## Protocol

```text
seeds = 1..10
volumes = low, medium, high
CAV penetration = 0.2, 0.5, 0.8
methods = fcfs, prediction_fcfs, prediction_coalition
duration = 300 s
runs = 270
```

Adaptive candidate:

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

Remote outputs were generated under:

```text
/public/home/xiaohei_0/hx/my_paper01_paper_r1_seed1_5_f2424f6
/public/home/xiaohei_0/hx/my_paper01_paper_r1_seed6_10_f2424f6
```

The summary artifacts were copied back to ignored local report directories:

```text
sim/prototype/reports/paper_r1_robustness_seed1_5_lmh_pen20_50_80_d300
sim/prototype/reports/paper_r1_robustness_seed6_10_lmh_pen20_50_80_d300
```

Generated outputs remain ignored by Git; this report records verified values only.

## Aggregate Result

| Method | Runs | Throughput up | Mean travel time down | Mean max wait down | Max wait down | Waiting Gini down | Conflict pairs down | Near conflicts down | Min PET up | Mean PET up |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fcfs` | 90 | 36.01 | 141.91 | 79.28 | 258.48 | 0.6451 | 137.72 | 1.51 | 3.13 | 89.67 |
| `prediction_fcfs` | 90 | 36.01 | 141.91 | 79.28 | 258.48 | 0.6451 | 137.72 | 1.51 | 3.13 | 89.67 |
| Adaptive gate | 90 | 37.03 | 137.28 | 77.95 | 259.46 | 0.6521 | 153.86 | 1.61 | 3.46 | 91.35 |

`prediction_fcfs` is identical to `fcfs` in this workload because the current heuristic priority predictor does not change the effective release behavior without the coalition release-set mechanism. This is useful as a sanity check: the observed gain comes from the coalition/adaptive release mechanism, not from the prediction-FCFS baseline.

## Delta vs FCFS

Positive deltas are better only for throughput and PET. Negative deltas are better for travel time, waiting, Gini, and conflicts.

| Metric | Adaptive - FCFS | Reading |
| --- | ---: | --- |
| Throughput | +1.02 vehicles/run | better |
| Mean observed travel time | -4.63 s | better |
| Mean max waiting time | -1.32 s | better |
| Max waiting time | +0.99 s | worse |
| Waiting Gini | +0.0070 | worse |
| Conflict-pair count | +16.13 | worse |
| Near-conflict count | +0.10 | worse |
| Min PET | +0.34 s | better in aggregate |
| Mean PET | +1.68 s | better |

R2 strengthens the efficiency evidence: adaptive improves throughput and travel time over the full grid. It weakens the safety-superiority wording: near-conflict count and conflict-pair count increase in aggregate, even though aggregate PET improves.

## Pairwise Check vs FCFS

Each pair matches seed, demand level, and CAV penetration.

| Metric | Preferred direction | Wins | Ties | Losses | Mean delta |
| --- | --- | ---: | ---: | ---: | ---: |
| Throughput | higher | 36 | 21 | 33 | +1.022 |
| Mean travel time | lower | 66 | 0 | 24 | -4.628 s |
| Mean max wait | lower | 44 | 0 | 46 | -1.322 s |
| Max wait | lower | 25 | 25 | 40 | +0.986 s |
| Waiting Gini | lower | 34 | 0 | 56 | +0.007 |
| Conflict pairs | lower | 13 | 37 | 40 | +16.133 |
| Near conflicts | lower | 9 | 70 | 11 | +0.100 |
| Min PET | higher | 25 | 41 | 24 | +0.336 s |
| Mean PET | higher | 62 | 0 | 28 | +1.677 s |

## CAV Penetration Sensitivity

The important interpretation is that "largest relative improvement" is not the same as "best absolute performance".

| CAV penetration | Method | Throughput up | Mean travel time down | Near conflicts down | Min PET up | Mean PET up | Waiting Gini down |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.2 | `fcfs` | 45.57 | 124.10 | 3.40 | 1.62 | 91.72 | 0.684 |
| 0.2 | Adaptive gate | 49.10 | 116.79 | 3.57 | 1.58 | 92.65 | 0.696 |
| 0.5 | `fcfs` | 33.10 | 147.49 | 0.93 | 3.15 | 86.69 | 0.634 |
| 0.5 | Adaptive gate | 33.40 | 142.04 | 1.03 | 3.28 | 87.95 | 0.642 |
| 0.8 | `fcfs` | 29.37 | 154.14 | 0.20 | 4.61 | 90.60 | 0.617 |
| 0.8 | Adaptive gate | 28.60 | 153.01 | 0.23 | 5.52 | 93.44 | 0.618 |

Adaptive minus FCFS by CAV penetration:

| CAV penetration | Throughput delta | Travel-time delta | Near-conflict delta | Min-PET delta | Mean-PET delta | Gini delta |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.2 | +3.53 | -7.30 s | +0.17 | -0.04 s | +0.92 s | +0.012 |
| 0.5 | +0.30 | -5.46 s | +0.10 | +0.13 s | +1.27 s | +0.008 |
| 0.8 | -0.77 | -1.13 s | +0.03 | +0.91 s | +2.84 s | +0.001 |

Interpretation:

- At 20% CAV penetration, the relative efficiency gain is largest because FCFS has more uncoordinated HDV interference and more room for improvement. However, this is also the riskiest setting: near conflicts increase and min PET does not improve.
- At 80% CAV penetration, absolute safety indicators are strongest: near conflicts are lowest and PET is highest. But the current release cap limits efficiency, so adaptive no longer improves throughput.
- This does not contradict the usual expectation that higher CAV penetration should improve controllability. It shows that the current prototype does not yet exploit high CAV controllability because the release set is capped at two base vehicles plus one adaptive extra vehicle.

## By Volume And Penetration

| Volume | Penetration | Throughput delta | Travel-time delta | Near-conflict delta | Min-PET delta | Mean-PET delta | Gini delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low | 0.2 | +5.20 | -9.35 s | +0.40 | -0.11 s | +1.07 s | +0.026 |
| low | 0.5 | +1.40 | -10.84 s | +0.50 | +0.39 s | +2.29 s | +0.018 |
| low | 0.8 | -0.70 | -2.97 s | +0.10 | +1.86 s | +0.23 s | +0.005 |
| medium | 0.2 | +3.50 | -8.71 s | +0.10 | -0.06 s | +0.21 s | +0.003 |
| medium | 0.5 | -0.40 | -3.22 s | -0.20 | +0.19 s | +1.02 s | -0.003 |
| medium | 0.8 | -1.00 | -0.20 s | +0.00 | -0.15 s | +2.92 s | -0.003 |
| high | 0.2 | +1.90 | -3.86 s | +0.00 | +0.06 s | +1.48 s | +0.006 |
| high | 0.5 | -0.10 | -2.30 s | +0.00 | -0.18 s | +0.48 s | +0.009 |
| high | 0.8 | -0.60 | -0.21 s | +0.00 | +1.02 s | +5.39 s | +0.001 |

The cleanest balanced setting remains `medium / 0.5`: adaptive improves travel time, near conflicts, min PET, mean PET, and waiting Gini, with only a small throughput loss. The riskiest setting is `low / 0.2`, where efficiency improves sharply but near conflicts and low-PET cases worsen.

## Why Higher CAV Penetration Does Not Automatically Improve Throughput Here

The route generator keeps demand fixed for each volume and only changes vehicle type:

```text
is_cav = rng.random() < penetration
```

However, the closed-loop controller only applies hold/release commands to CAVs. HDVs are not directly controlled. Therefore, as CAV penetration increases, more vehicles become subject to the current conservative release rule.

The current adaptive gate can release:

```text
base release cap = 2
adaptive max release cap = 3
```

This cap is intentionally conservative for safety, but it also means high-CAV settings cannot fully exploit the larger controllable fleet. The high-CAV result should therefore be interpreted as a limitation of the current release-cap design, not as evidence that CAV penetration is harmful.

## Worst Adaptive Min-PET Cases

| Seed | Volume | Penetration | Adaptive min PET | FCFS min PET | Adaptive near conflicts | FCFS near conflicts | Adaptive travel time | FCFS travel time | Adaptive throughput | FCFS throughput |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | low | 0.2 | 0.20 | 1.00 | 6 | 5 | 93.92 | 106.45 | 52 | 42 |
| 4 | medium | 0.2 | 0.90 | 1.40 | 3 | 4 | 103.49 | 114.14 | 61 | 51 |
| 1 | medium | 0.2 | 0.90 | 0.90 | 14 | 16 | 86.94 | 86.96 | 66 | 69 |
| 3 | medium | 0.2 | 0.90 | 0.90 | 4 | 5 | 109.74 | 116.27 | 61 | 51 |
| 1 | low | 0.2 | 0.90 | 0.90 | 8 | 8 | 79.16 | 82.69 | 47 | 42 |
| 1 | high | 0.2 | 0.90 | 0.90 | 8 | 8 | 103.37 | 102.45 | 68 | 71 |
| 6 | low | 0.5 | 0.90 | 1.60 | 3 | 0 | 82.27 | 112.75 | 41 | 33 |
| 9 | low | 0.2 | 0.90 | 0.80 | 5 | 5 | 69.40 | 89.16 | 62 | 59 |

The worst case confirms the tradeoff: adaptive can produce a large efficiency gain while also creating a very small local PET. This should motivate a safety-guard refinement, not be hidden.

## Interpretation

R2 supports a narrower but stronger paper claim than C1 alone:

```text
The adaptive route-zone coalition allocator improves aggregate efficiency and PET over a full T-junction demand/penetration grid, but it does not yet provide aggregate near-conflict or fairness superiority.
```

What R2 supports:

- Robust travel-time reduction over the full grid.
- Throughput improvement in aggregate and especially at 20% CAV penetration.
- Aggregate min-PET and mean-PET improvement.
- Clear mechanism diagnosis: low penetration gives large efficiency gains but tight safety margins; high penetration gives safer PET behavior but is limited by the release cap.

What R2 does not support:

- A claim that adaptive is safer on every safety metric.
- A claim that higher CAV penetration is worse in general.
- A claim that the current release cap fully exploits high CAV penetration.
- A claim that the fairness mechanism improves waiting inequality.

## Next Step

The next experiment should be a targeted CAV-penetration mechanism check, not another broad sweep.

Recommended R3:

```text
high-CAV release-cap sensitivity
penetration = 0.8
volumes = low, medium, high
seeds = 1..10
duration = 300 s
variants:
  current cap: base 2, adaptive 3
  wider cap: base 3, adaptive 4
  conservative reference: base 2, adaptive disabled
```

Purpose:

- Check whether high-CAV throughput loss is caused by the current release cap.
- Preserve PET and near-conflict safeguards while allowing more CAVs to use their controllability.
- Avoid wrongly concluding that high CAV penetration is bad.

No final paper claim should be made until R3 confirms whether the high-CAV limitation is a parameter/cap issue or a deeper mechanism issue.
