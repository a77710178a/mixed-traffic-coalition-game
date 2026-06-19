# R5 Adaptive-Gate Trigger Sensitivity Report

Date: 2026-06-19

Scenario: T-junction route-zone geometry, 80% CAV penetration, mixed CAV/HDV traffic, unsignalized intersection.

R5 follows the R3/R4 high-CAV release-cap diagnosis. R3 was efficient but safety margins became thinner; R4 preserved safety but the adaptive gate almost never triggered. R5 tests a middle trigger setting while keeping the conservative base release cap.

## Protocol

```text
seeds = 1..10
volumes = low, medium, high
CAV penetration = 0.8
methods = prediction_coalition
duration = 300 s
runs = 30
```

R5 candidate:

```text
max_release_count = 2
adaptive_release_enabled = true
adaptive_max_release_count = 4
safe_arrival_gap_s = 1.2
adaptive_min_conflict_arrival_gap_s = 3.6
adaptive_max_occupancy = 1
fairness_weight = 0.0
cav_waiting_tiebreaker_weight = 0.1
```

Remote output:

```text
/public/home/xiaohei_0/hx/my_paper01_paper_r5_occ1_cgap36_a5a689d
```

## Aggregate High-CAV Result

| Variant | Runs | Throughput up | Mean travel time down | Mean max wait down | Max wait down | Waiting Gini down | Conflict pairs down | Near conflicts down | Min PET up | Mean PET up | Min entry gap up |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R2 FCFS | 30 | 29.37 | 154.14 | 89.05 | 261.03 | 0.617 | 90.33 | 0.20 | 4.61 | 90.60 | 6.72 |
| R2 adaptive cap2/3 | 30 | 28.60 | 153.01 | 90.83 | 269.14 | 0.618 | 93.07 | 0.23 | 5.52 | 93.44 | 7.30 |
| R3 coarse cap3/4 | 30 | 29.97 | 147.07 | 88.55 | 272.86 | 0.628 | 100.80 | 0.27 | 4.36 | 96.27 | 6.10 |
| R4 gated cap2/4 occ0 cgap2.4 | 30 | 28.70 | 152.74 | 90.65 | 270.34 | 0.619 | 93.03 | 0.27 | 5.51 | 93.08 | 7.25 |
| R5 gated cap2/4 occ1 cgap3.6 | 30 | 29.83 | 149.08 | 87.16 | 263.25 | 0.622 | 97.87 | 0.30 | 5.38 | 95.58 | 7.00 |

## Deltas

R5 relative to R2 adaptive:

| Metric | R5 - R2 adaptive | Reading |
| --- | ---: | --- |
| Throughput | +1.23 vehicles/run | clear efficiency recovery |
| Mean travel time | -3.94 s | clear efficiency recovery |
| Mean max wait | -3.67 s | better |
| Max wait | -5.88 s | better |
| Conflict pairs | +4.80 | worse |
| Near conflicts | +0.07 | worse |
| Min PET | -0.14 s | slightly worse |
| Mean PET | +2.14 s | better |
| Waiting Gini | +0.004 | slightly worse |

R5 relative to R3:

| Metric | R5 - R3 | Reading |
| --- | ---: | --- |
| Throughput | -0.13 vehicles/run | nearly as efficient |
| Mean travel time | +2.01 s | less efficient than R3 but still improved vs R2 |
| Conflict pairs | -2.93 | safer than R3 |
| Min PET | +1.02 s | much safer than R3 |
| Max wait | -9.60 s | better than R3 |

R5 relative to R4:

| Metric | R5 - R4 | Reading |
| --- | ---: | --- |
| Throughput | +1.13 vehicles/run | better |
| Mean travel time | -3.66 s | better |
| Conflict pairs | +4.83 | worse |
| Min PET | -0.13 s | slightly worse |
| Mean PET | +2.51 s | better |

## Release-Set Diagnosis

| Variant | Decision steps | Steps with release count > 2 | Share |
| --- | ---: | ---: | ---: |
| R3 coarse cap3/4 | 87,624 | 84,983 | 97.0% |
| R4 gated cap2/4 occ0 cgap2.4 | 87,624 | 387 | 0.44% |
| R5 gated cap2/4 occ1 cgap3.6 | 87,624 | 2,711 | 3.09% |

R5 is a real middle point: it uses larger release sets far more often than R4, but far less aggressively than R3.

## By Volume

| Volume | Variant | Throughput up | Mean travel time down | Near conflicts down | Min PET up | Mean PET up | Conflict pairs down |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| low | R2 adaptive cap2/3 | 26.20 | 135.67 | 0.20 | 6.45 | 84.63 | 65.70 |
| low | R5 gated cap2/4 occ1 cgap3.6 | 28.30 | 127.62 | 0.30 | 6.07 | 91.78 | 72.00 |
| medium | R2 adaptive cap2/3 | 29.10 | 157.36 | 0.30 | 3.85 | 95.81 | 102.90 |
| medium | R5 gated cap2/4 occ1 cgap3.6 | 30.60 | 153.39 | 0.40 | 3.82 | 96.63 | 111.50 |
| high | R2 adaptive cap2/3 | 30.50 | 166.01 | 0.20 | 6.26 | 99.89 | 110.60 |
| high | R5 gated cap2/4 occ1 cgap3.6 | 30.60 | 166.23 | 0.20 | 6.25 | 98.35 | 110.10 |

Most of R5's efficiency recovery comes from low and medium demand. High demand changes little compared with R2 adaptive.

## Interpretation

R5 is currently the best mechanism diagnosis for high-CAV controllability:

- It recovers most of the R3 efficiency signal without the large min-PET loss of R3.
- It increases release-set size only 3.09% of decision steps, so it is much less aggressive than R3.
- It still increases conflict-pair count and near-conflict count relative to R2 adaptive, so it is not yet a clean final method.

Paper-safe wording:

```text
High-CAV efficiency can be recovered by relaxing adaptive release eligibility, but the release trigger must be safety-shaped; otherwise conflict load increases.
```

## Next Run R6

Recommended next variant:

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

Rationale: keep R5's more permissive occupancy trigger, but cap the adaptive release set at 3 instead of 4. The goal is to retain part of R5's efficiency recovery while reducing conflict pairs and near conflicts.

If R6 preserves most of the travel-time improvement and lowers conflict load, it becomes the stronger high-CAV candidate. If R6 collapses back toward R4, then the next design change should be an explicit projected-PET guard rather than more scalar threshold tuning.
