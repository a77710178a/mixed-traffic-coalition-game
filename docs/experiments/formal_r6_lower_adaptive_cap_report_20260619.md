# R6 Lower Adaptive-Cap Trigger Report

Date: 2026-06-19

Scenario: T-junction route-zone geometry, 80% CAV penetration, mixed CAV/HDV traffic, unsignalized intersection.

R6 follows R5. R5 recovered high-CAV efficiency by allowing one occupied conflict-zone vehicle and a stricter conflict-arrival gap, but conflict-pair and near-conflict counts increased. R6 tests whether lowering the adaptive cap from 4 to 3 can preserve the efficiency gain while reducing conflict load.

## Protocol

```text
seeds = 1..10
volumes = low, medium, high
CAV penetration = 0.8
methods = prediction_coalition
duration = 300 s
runs = 30
```

R6 candidate:

```text
max_release_count = 2
adaptive_release_enabled = true
adaptive_max_release_count = 3
safe_arrival_gap_s = 1.2
adaptive_min_conflict_arrival_gap_s = 3.6
adaptive_max_occupancy = 1
fairness_weight = 0.0
cav_waiting_tiebreaker_weight = 0.1
```

Remote outputs were generated in isolated directories to avoid concurrent writes to the same geometry artifact:

```text
/public/home/xiaohei_0/hx/my_paper01_paper_r6_occ1_cgap36_amr3_seed1_5_1b02a15
/public/home/xiaohei_0/hx/my_paper01_paper_r6_occ1_cgap36_amr3_seed6_10_1b02a15
```

The first shared-directory launch failed with a `JSONDecodeError` while reading `route_geometry`, caused by two concurrent processes writing/reading the same geometry JSON. The reported R6 results are from the clean isolated rerun only.

## Aggregate High-CAV Result

| Variant | Runs | Throughput up | Mean travel time down | Mean max wait down | Max wait down | Waiting Gini down | Conflict pairs down | Near conflicts down | Min PET up | Mean PET up | Min entry gap up |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R2 FCFS | 30 | 29.37 | 154.14 | 89.05 | 261.03 | 0.617 | 90.33 | 0.20 | 4.61 | 90.60 | 6.72 |
| R2 adaptive cap2/3 | 30 | 28.60 | 153.01 | 90.83 | 269.14 | 0.618 | 93.07 | 0.23 | 5.52 | 93.44 | 7.30 |
| R3 coarse cap3/4 | 30 | 29.97 | 147.07 | 88.55 | 272.86 | 0.628 | 100.80 | 0.27 | 4.36 | 96.27 | 6.10 |
| R5 cap2/adapt4 occ1 cgap3.6 | 30 | 29.83 | 149.08 | 87.16 | 263.25 | 0.622 | 97.87 | 0.30 | 5.38 | 95.58 | 7.00 |
| R6 cap2/adapt3 occ1 cgap3.6 | 30 | 30.00 | 148.73 | 86.76 | 263.43 | 0.625 | 99.30 | 0.37 | 5.31 | 95.25 | 6.96 |

## Deltas

R6 relative to R2 adaptive:

| Metric | R6 - R2 adaptive | Reading |
| --- | ---: | --- |
| Throughput | +1.40 vehicles/run | efficiency improves |
| Mean travel time | -4.29 s | efficiency improves |
| Mean max wait | -4.07 s | better |
| Max wait | -5.71 s | better |
| Conflict pairs | +6.23 | worse |
| Near conflicts | +0.13 | worse |
| Min PET | -0.21 s | worse |
| Mean PET | +1.80 s | better |

R6 relative to R5:

| Metric | R6 - R5 | Reading |
| --- | ---: | --- |
| Throughput | +0.17 vehicles/run | nearly unchanged |
| Mean travel time | -0.35 s | nearly unchanged |
| Conflict pairs | +1.43 | worse |
| Near conflicts | +0.07 | worse |
| Min PET | -0.07 s | slightly worse |
| Mean PET | -0.34 s | slightly worse |

## Release-Set Diagnosis

| Variant | Decision steps | Steps with release count > 2 | Share |
| --- | ---: | ---: | ---: |
| R5 cap2/adapt4 occ1 cgap3.6 | 87,624 | 2,711 | 3.09% |
| R6 cap2/adapt3 occ1 cgap3.6 | 87,624 | 2,473 | 2.82% |

R6 did not meaningfully reduce the frequency of expanded release sets. It mostly converts occasional four-vehicle releases into three-vehicle releases, but the low-demand setting still becomes more aggressive.

## By Volume

| Volume | Variant | Throughput up | Mean travel time down | Near conflicts down | Min PET up | Mean PET up | Conflict pairs down |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| low | R2 adaptive cap2/3 | 26.20 | 135.67 | 0.20 | 6.45 | 84.63 | 65.70 |
| low | R5 cap2/adapt4 occ1 cgap3.6 | 28.30 | 127.62 | 0.30 | 6.07 | 91.78 | 72.00 |
| low | R6 cap2/adapt3 occ1 cgap3.6 | 29.60 | 123.65 | 0.50 | 5.86 | 92.21 | 82.30 |
| medium | R2 adaptive cap2/3 | 29.10 | 157.36 | 0.30 | 3.85 | 95.81 | 102.90 |
| medium | R5 cap2/adapt4 occ1 cgap3.6 | 30.60 | 153.39 | 0.40 | 3.82 | 96.63 | 111.50 |
| medium | R6 cap2/adapt3 occ1 cgap3.6 | 29.70 | 156.52 | 0.40 | 3.82 | 94.62 | 104.60 |
| high | R2 adaptive cap2/3 | 30.50 | 166.01 | 0.20 | 6.26 | 99.89 | 110.60 |
| high | R5 cap2/adapt4 occ1 cgap3.6 | 30.60 | 166.23 | 0.20 | 6.25 | 98.35 | 110.10 |
| high | R6 cap2/adapt3 occ1 cgap3.6 | 30.70 | 166.01 | 0.20 | 6.26 | 98.90 | 111.00 |

The R6 aggregate efficiency gain is mainly driven by low-demand runs, where conflict-pair and near-conflict counts also worsen. It is therefore not a cleaner candidate than R5.

## Interpretation

R6 fails the intended safety-efficiency refinement:

- It does not reduce conflict load relative to R5.
- It increases near conflicts relative to R5.
- It preserves efficiency mostly by becoming more aggressive in low-demand runs.

This suggests that scalar cap tuning has reached a useful boundary. The next method change should not be another cap-only sweep. It should add an explicit projected-PET or projected conflict-arrival guard for adaptive extra releases.

## Next Method Step

Recommended design direction:

```text
Before adding an adaptive extra CAV, estimate its projected conflict-zone entry time against every currently released vehicle.
Allow the extra release only if all conflicting route pairs satisfy a projected PET threshold.
```

Suggested first guard:

```text
base max_release_count = 2
adaptive_max_release_count = 4
adaptive_max_occupancy = 1
adaptive_min_conflict_arrival_gap_s = 3.6
projected_min_pet_s = 4.0
```

This should be implemented as a code-level guard and unit-tested before launching another remote batch. The first guard threshold should be larger than `adaptive_min_conflict_arrival_gap_s`; otherwise the existing conflict-arrival gap already dominates the new guard. R5 remains the best current high-CAV efficiency diagnostic, but it is not a final safety-clean method.
