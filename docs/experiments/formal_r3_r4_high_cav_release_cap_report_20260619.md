# R3/R4 High-CAV Release-Cap Mechanism Report

Date: 2026-06-19

Scenario: T-junction route-zone geometry, 80% CAV penetration, mixed CAV/HDV traffic, unsignalized intersection.

This report follows the R2 full-grid robustness result. R2 showed that the current adaptive gate has strong absolute PET behavior at 80% CAV penetration but weak throughput gain. R3 and R4 test whether that weakness is caused by the release-cap design.

## Protocol

Matched high-CAV workload:

```text
seeds = 1..10
volumes = low, medium, high
CAV penetration = 0.8
methods = prediction_coalition
duration = 300 s
runs per variant = 30
```

Compared rows:

```text
R2 FCFS reference
R2 adaptive cap2/3: base max_release_count = 2, adaptive_max_release_count = 3
R3 coarse wider cap3/4: base max_release_count = 3, adaptive_max_release_count = 4
R4 gated wider cap2/4: base max_release_count = 2, adaptive_max_release_count = 4
```

R4 includes the code correction in snapshot `01e043d`: the adaptive gate can keep adding safe extra CAVs until `adaptive_max_release_count` is reached, rather than adding at most one extra CAV.

Remote outputs:

```text
R3 seed1_5 = /public/home/xiaohei_0/hx/my_paper01_paper_r3_cap34_seed1_5_c00d0c8
R3 seed6_10 = /public/home/xiaohei_0/hx/my_paper01_paper_r3_cap34_seed6_10_c00d0c8
R4 base = /public/home/xiaohei_0/hx/my_paper01_paper_r4_adaptive24_01e043d
```

Summary artifacts were copied back to ignored local report directories under `sim/prototype/reports/`.

## Aggregate High-CAV Result

Higher is better for throughput and PET. Lower is better for travel time, conflicts, waiting Gini, and max wait.

| Variant | Runs | Throughput up | Mean travel time down | Mean max wait down | Max wait down | Waiting Gini down | Conflict pairs down | Near conflicts down | Min PET up | Mean PET up | Min entry gap up |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R2 FCFS | 30 | 29.37 | 154.14 | 89.05 | 261.03 | 0.617 | 90.33 | 0.20 | 4.61 | 90.60 | 6.72 |
| R2 adaptive cap2/3 | 30 | 28.60 | 153.01 | 90.83 | 269.14 | 0.618 | 93.07 | 0.23 | 5.52 | 93.44 | 7.30 |
| R3 coarse wider cap3/4 | 30 | 29.97 | 147.07 | 88.55 | 272.86 | 0.628 | 100.80 | 0.27 | 4.36 | 96.27 | 6.10 |
| R4 gated wider cap2/4 | 30 | 28.70 | 152.74 | 90.65 | 270.34 | 0.619 | 93.03 | 0.27 | 5.51 | 93.08 | 7.25 |

## Deltas

R3 relative to R2 adaptive:

| Metric | R3 - R2 adaptive | Reading |
| --- | ---: | --- |
| Throughput | +1.37 vehicles/run | efficiency recovers |
| Mean travel time | -5.95 s | efficiency improves |
| Near conflicts | +0.03 | slightly worse |
| Conflict pairs | +7.73 | worse |
| Min PET | -1.16 s | safety margin worsens |
| Mean PET | +2.82 s | aggregate spacing improves |
| Waiting Gini | +0.010 | worse |

R4 relative to R2 adaptive:

| Metric | R4 - R2 adaptive | Reading |
| --- | ---: | --- |
| Throughput | +0.10 vehicles/run | nearly unchanged |
| Mean travel time | -0.28 s | nearly unchanged |
| Near conflicts | +0.03 | slightly worse |
| Conflict pairs | -0.03 | unchanged |
| Min PET | -0.01 s | unchanged |
| Mean PET | -0.37 s | nearly unchanged |
| Waiting Gini | +0.001 | unchanged |

R4 relative to R3:

| Metric | R4 - R3 | Reading |
| --- | ---: | --- |
| Throughput | -1.27 vehicles/run | less efficient |
| Mean travel time | +5.67 s | less efficient |
| Conflict pairs | -7.77 | safer interaction load |
| Min PET | +1.15 s | safer worst-case margin |
| Waiting Gini | -0.008 | fairer |

## By Volume

| Volume | Variant | Throughput up | Mean travel time down | Near conflicts down | Min PET up | Mean PET up | Conflict pairs down |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| low | R2 adaptive cap2/3 | 26.20 | 135.67 | 0.20 | 6.45 | 84.63 | 65.70 |
| low | R3 coarse wider cap3/4 | 28.00 | 126.74 | 0.20 | 3.41 | 91.07 | 70.00 |
| low | R4 gated wider cap2/4 | 26.20 | 135.59 | 0.20 | 6.43 | 84.57 | 65.70 |
| medium | R2 adaptive cap2/3 | 29.10 | 157.36 | 0.30 | 3.85 | 95.81 | 102.90 |
| medium | R3 coarse wider cap3/4 | 30.40 | 151.55 | 0.40 | 3.85 | 96.05 | 114.10 |
| medium | R4 gated wider cap2/4 | 29.40 | 156.32 | 0.40 | 3.84 | 94.87 | 103.40 |
| high | R2 adaptive cap2/3 | 30.50 | 166.01 | 0.20 | 6.26 | 99.89 | 110.60 |
| high | R3 coarse wider cap3/4 | 31.50 | 162.92 | 0.20 | 5.82 | 101.68 | 118.30 |
| high | R4 gated wider cap2/4 | 30.50 | 166.30 | 0.20 | 6.27 | 99.80 | 110.00 |

## Release-Set Diagnosis

The release-set logs explain why R3 and R4 behave differently.

| Variant | Decision steps | Steps with release count > 2 | Share | Interpretation |
| --- | ---: | ---: | ---: | --- |
| R3 coarse wider cap3/4 | 87,624 | 84,983 | 97.0% | base cap 3 dominates, so more CAVs are released almost continuously |
| R4 gated wider cap2/4 | 87,624 | 387 | 0.44% | adaptive gate is too hard to trigger under `occupancy=0` and `cgap=2.4` |

This is the key mechanism finding. R3 confirms that high-CAV efficiency can be recovered by allowing larger release sets, but the coarse base cap creates a thinner safety margin. R4 confirms that the current geometry-aware adaptive gate preserves the R2 safety behavior, but it triggers so rarely that it cannot recover high-CAV efficiency.

## Interpretation

Do not interpret R2 as "low CAV is better than high CAV." The correct interpretation is:

```text
High CAV penetration has stronger absolute PET and near-conflict behavior, but the current conservative release-cap design underuses the larger controllable CAV fleet.
```

R3/R4 refine that statement:

- The high-CAV efficiency weakness is indeed release-cap related.
- Simply raising the base release cap from 2 to 3 recovers efficiency but worsens conflict load and min PET.
- Keeping the base cap at 2 and relying only on the current adaptive gate is too conservative; extra releases almost never trigger.
- The next method step should tune adaptive-gate eligibility, not raise the base cap.

## Claim Status

Supported:

- High-CAV inefficiency is a mechanism limitation of the current release-cap design.
- A larger release set can recover high-CAV throughput and travel-time performance.
- Geometry-aware gating is necessary because coarse release expansion worsens safety indicators.

Not supported:

- R3 should not replace the main method because it reduces min PET and increases conflict-pair count.
- R4 should not be presented as a new high-CAV improvement because its aggregate behavior is nearly the same as R2.
- The paper should not claim that higher CAV penetration is harmful.

## Next Run R5

Run a targeted adaptive-gate trigger sensitivity, keeping the conservative base cap:

```text
base max_release_count = 2
adaptive_max_release_count = 4
CAV penetration = 0.8
volumes = low, medium, high
seeds = 1..10
duration = 300 s
```

Recommended first R5 variant:

```text
adaptive_max_occupancy = 1
adaptive_min_conflict_arrival_gap_s = 3.6
```

Rationale: `adaptive_max_occupancy=0` makes R4 trigger only 0.44% of decision steps. Allowing one vehicle in the conflict zone should increase trigger frequency, while the stricter `3.6 s` conflict-arrival gap should protect PET better than R3.

If R5 remains too conservative, test `adaptive_min_conflict_arrival_gap_s=2.4` with `adaptive_max_occupancy=1`. If R5 worsens PET or near conflicts, add an explicit projected-PET guard before any broader full-grid run.
