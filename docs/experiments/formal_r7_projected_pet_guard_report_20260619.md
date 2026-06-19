# R7 Projected-PET Adaptive Guard Report

Date: 2026-06-19

Scenario: T-junction route-zone geometry, 80% CAV penetration, mixed CAV/HDV traffic, unsignalized intersection.

R7 follows R5 and R6. R5 recovered high-CAV efficiency but increased conflict load. R6 lowered the adaptive release cap, but did not reduce conflict-pair or near-conflict counts. R7 tests whether a direct projected-PET guard can shape the adaptive extra release more safely than cap-only tuning.

## Protocol

```text
seeds = 1..10
volumes = low, medium, high
CAV penetration = 0.8
methods = prediction_coalition
duration = 300 s
runs = 30
```

R7 candidate:

```text
max_release_count = 2
adaptive_release_enabled = true
adaptive_max_release_count = 4
safe_arrival_gap_s = 1.2
adaptive_min_conflict_arrival_gap_s = 3.6
adaptive_max_occupancy = 1
projected_min_pet_s = 4.0
fairness_weight = 0.0
cav_waiting_tiebreaker_weight = 0.1
```

Remote outputs were generated in isolated directories:

```text
/public/home/xiaohei_0/hx/my_paper01_paper_r7_petguard4_seed1_5_8b85438
/public/home/xiaohei_0/hx/my_paper01_paper_r7_petguard4_seed6_10_8b85438
```

Summary artifacts were copied back to ignored local report directories under `sim/prototype/reports/`.

## Aggregate High-CAV Result

Higher is better for throughput and PET. Lower is better for travel time, conflicts, waiting Gini, and max wait.

| Variant | Runs | Throughput up | Mean travel time down | Mean max wait down | Max wait down | Waiting Gini down | Conflict pairs down | Near conflicts down | Min PET up | Mean PET up | Min entry gap up |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R2 FCFS | 30 | 29.37 | 154.14 | 89.05 | 261.03 | 0.617 | 90.33 | 0.20 | 4.61 | 90.60 | 6.72 |
| R2 adaptive cap2/3 | 30 | 28.60 | 153.01 | 90.83 | 269.14 | 0.618 | 93.07 | 0.23 | 5.52 | 93.44 | 7.30 |
| R3 coarse cap3/4 | 30 | 29.97 | 147.07 | 88.55 | 272.86 | 0.628 | 100.80 | 0.27 | 4.36 | 96.27 | 6.10 |
| R5 cap2/adapt4 occ1 cgap3.6 | 30 | 29.83 | 149.08 | 87.16 | 263.25 | 0.622 | 97.87 | 0.30 | 5.38 | 95.58 | 7.00 |
| R6 cap2/adapt3 occ1 cgap3.6 | 30 | 30.00 | 148.73 | 86.76 | 263.43 | 0.625 | 99.30 | 0.37 | 5.31 | 95.25 | 6.96 |
| R7 projected PET guard4 | 30 | 29.30 | 151.27 | 88.95 | 265.19 | 0.619 | 95.10 | 0.30 | 5.25 | 94.78 | 6.98 |

## Deltas

R7 relative to R2 adaptive:

| Metric | R7 - R2 adaptive | Reading |
| --- | ---: | --- |
| Throughput | +0.70 vehicles/run | efficiency improves, but less than R5/R6 |
| Mean travel time | -1.74 s | travel time improves |
| Mean max wait | -1.88 s | better |
| Max wait | -3.95 s | better |
| Conflict pairs | +2.03 | worse than R2 adaptive |
| Near conflicts | +0.07 | worse than R2 adaptive |
| Min PET | -0.27 s | worse than R2 adaptive |
| Mean PET | +1.34 s | better than R2 adaptive |
| Waiting Gini | +0.001 | nearly unchanged |

R7 relative to R5:

| Metric | R7 - R5 | Reading |
| --- | ---: | --- |
| Throughput | -0.53 vehicles/run | less efficient |
| Mean travel time | +2.19 s | less efficient |
| Mean max wait | +1.79 s | worse |
| Max wait | +1.94 s | worse |
| Conflict pairs | -2.77 | safer interaction load |
| Near conflicts | +0.00 | unchanged |
| Min PET | -0.13 s | slightly lower |
| Mean PET | -0.80 s | lower |
| Waiting Gini | -0.004 | slightly fairer |

R7 relative to R6:

| Metric | R7 - R6 | Reading |
| --- | ---: | --- |
| Throughput | -0.70 vehicles/run | less efficient |
| Mean travel time | +2.55 s | less efficient |
| Conflict pairs | -4.20 | lower conflict load |
| Near conflicts | -0.07 | lower than R6 |
| Min PET | -0.06 s | nearly unchanged |
| Mean PET | -0.46 s | slightly lower |
| Min entry gap | +0.02 s | nearly unchanged |

## Release-Set Diagnosis

| Variant | Decision steps | Steps with release count > 2 | Share |
| --- | ---: | ---: | ---: |
| R3 coarse cap3/4 | 87,624 | 84,983 | 97.0% |
| R4 gated cap2/4 occ0 cgap2.4 | 87,624 | 387 | 0.44% |
| R5 cap2/adapt4 occ1 cgap3.6 | 87,624 | 2,711 | 3.09% |
| R6 cap2/adapt3 occ1 cgap3.6 | 87,624 | 2,473 | 2.82% |
| R7 projected PET guard4 | 87,624 | 2,261 | 2.58% |

R7 does not collapse to the very conservative R4 behavior. The adaptive gate still triggers more than two releases in 2.58% of decision steps, but the projected-PET guard reduces expanded releases relative to R5 and R6.

R7 release-set distribution:

| Release count | Decision steps | Share |
| ---: | ---: | ---: |
| 1 | 1,088 | 1.24% |
| 2 | 84,275 | 96.18% |
| 3 | 654 | 0.75% |
| 4 | 1,607 | 1.83% |

By volume:

| Volume | Decision steps | Steps with release count > 2 | Share |
| --- | ---: | ---: | ---: |
| low | 29,163 | 758 | 2.60% |
| medium | 29,203 | 560 | 1.92% |
| high | 29,258 | 943 | 3.22% |

## By Volume

| Volume | Variant | Throughput up | Mean travel time down | Near conflicts down | Min PET up | Mean PET up | Conflict pairs down |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| low | R2 adaptive cap2/3 | 26.20 | 135.67 | 0.20 | 6.45 | 84.63 | 65.70 |
| low | R5 cap2/adapt4 occ1 cgap3.6 | 28.30 | 127.62 | 0.30 | 6.07 | 91.78 | 72.00 |
| low | R6 cap2/adapt3 occ1 cgap3.6 | 29.60 | 123.65 | 0.50 | 5.86 | 92.21 | 82.30 |
| low | R7 projected PET guard4 | 27.40 | 131.52 | 0.30 | 6.18 | 89.46 | 68.10 |
| medium | R2 adaptive cap2/3 | 29.10 | 157.36 | 0.30 | 3.85 | 95.81 | 102.90 |
| medium | R5 cap2/adapt4 occ1 cgap3.6 | 30.60 | 153.39 | 0.40 | 3.82 | 96.63 | 111.50 |
| medium | R6 cap2/adapt3 occ1 cgap3.6 | 29.70 | 156.52 | 0.40 | 3.82 | 94.62 | 104.60 |
| medium | R7 projected PET guard4 | 29.90 | 155.82 | 0.40 | 3.83 | 96.85 | 107.10 |
| high | R2 adaptive cap2/3 | 30.50 | 166.01 | 0.20 | 6.26 | 99.89 | 110.60 |
| high | R5 cap2/adapt4 occ1 cgap3.6 | 30.60 | 166.23 | 0.20 | 6.25 | 98.35 | 110.10 |
| high | R6 cap2/adapt3 occ1 cgap3.6 | 30.70 | 166.01 | 0.20 | 6.26 | 98.90 | 111.00 |
| high | R7 projected PET guard4 | 30.60 | 166.48 | 0.20 | 5.74 | 98.05 | 110.10 |

## Interpretation

R7 is a useful mechanism diagnostic, but not a clean final winner:

- It reduces conflict-pair count relative to R5 and R6, so the projected-PET guard is doing real work.
- It preserves a modest efficiency gain over R2 adaptive, but gives back much of R5/R6's efficiency recovery.
- It does not reduce near conflicts relative to R5, and min PET is slightly lower than R5/R6.
- It is therefore better described as a safety-shaped refinement knob than as the final high-CAV method.

Paper-safe wording:

```text
Projected-PET gating can reduce the conflict load introduced by more permissive high-CAV adaptive release, but the current arrival-time proxy is conservative and trades away part of the efficiency recovery.
```

Not supported:

```text
R7 dominates R5.
R7 fully solves the high-CAV safety-efficiency tradeoff.
The current projected-arrival estimate is accurate enough for a final PET guarantee.
```

## Next Step

Do not run another cap-only sweep. The next mechanism work should inspect R7's blocked/allowed extra releases and improve the projected-arrival model or guard condition.

Recommended next diagnostic:

```text
For R5 and R7, sample decision steps where release count differs.
Record candidate route pair, estimated arrival times, conflict relation, actual entry/exit times, and realized PET.
Then decide whether the projected-PET threshold is too strict, whether the arrival-time proxy is biased, or whether the conflict matrix is missing local geometry detail.
```

R5 remains the strongest high-CAV efficiency diagnostic. R7 is the stronger evidence that safety-shaped adaptive release is necessary, but it is not yet the best final candidate.
