# Remote SUMO Smoke Test

Date: 2026-06-16

Remote directory:

```text
/public/home/xiaohei_0/hx/my_paper01/sim/prototype
```

Environment:

```text
conda env: sumoenv
SUMO: 1.23.1
GPU server: gpuadmin1
```

## What Was Verified

The first SUMO prototype can now:

1. generate a four-leg unsignalized intersection network;
2. generate sorted mixed CAV/HDV route files;
3. run SUMO through TraCI;
4. log per-step vehicle states;
5. extract conflict-zone entry/exit events;
6. generate HDV yield/non-yield labels.

## Smoke Test Runs

| Run ID | Volume | Seed | CAV penetration | Duration | Vehicles | State rows | Conflict events | HDV events | CAV events | Labels | Non-yield | Yield |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seed1_low_pen50 | low | 1 | 0.5 | 120 s | 40 | 9981 | 37 | 19 | 18 | 45 | 6 | 39 |
| seed2_medium_pen50 | medium | 2 | 0.5 | 120 s | not recorded in summary | not recorded in summary | 45 | 17 | 28 | 44 | 10 | 34 |
| seed3_high_pen50 | high | 3 | 0.5 | 120 s | not recorded in summary | not recorded in summary | 54 | 30 | 24 | 68 | 6 | 62 |

## Issues Found And Fixed

1. Route vehicles were initially not sorted by departure time. SUMO ignored many vehicles. Fixed by sorting generated vehicles by `depart`.
2. The conflict center was initially assumed to be `(0, 0)`. SUMO/netconvert shifted the generated center to `(120, 120)`. Fixed by reading junction `C` from `four_leg.net.xml`.

## Current Data Quality Note

The prototype produces labels, but the class distribution is still yield-heavy. This is acceptable for the first pipeline smoke test. Before training the prediction model, run a multi-seed label sanity experiment and tune scenario pressure or label thresholds if non-yield samples remain too sparse.

## Next Recommended Step

Create a batch runner for P0-E1:

```text
seeds: 1-10
volumes: low / medium / high
penetration: 0.2 / 0.5 / 0.8
duration: 300 s
```

The output should aggregate label counts by volume, seed, penetration, HDV behavior profile, and confidence level.

