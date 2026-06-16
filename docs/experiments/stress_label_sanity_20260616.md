# Stress Label Sanity Check

Date: 2026-06-16

Remote directory:

```text
/public/home/xiaohei_0/hx/my_paper01/sim/prototype
```

Configuration:

```text
sim/prototype/config/stress_scenario.json
```

Batch:

```text
seeds: 5, 6
volumes: low, medium, high
CAV penetration: 0.2, 0.5, 0.8
duration: 180 s
total runs: 18
```

## Scenario Changes

Compared with `default_scenario.json`, the stress scenario:

1. increases demand levels;
2. increases left-turn ratio;
3. increases aggressive HDV share to `0.65`;
4. slightly enlarges the conflict-zone radius;
5. uses a more permissive priority time margin.

## Aggregate Result

| Runs | Vehicles | Conflict events | Labels | HDV takes priority | Strict non-yield | High confidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 18 | 1989 | 1381 | 1813 | 840 | 221 | 1564 |

Ratios:

```text
HDV takes-priority ratio: 46.33%
Strict non-yield ratio:   12.19%
```

## Distribution By CAV Penetration

| CAV penetration | Labels | HDV takes priority | Ratio | Strict non-yield |
| ---: | ---: | ---: | ---: | ---: |
| 0.2 | 922 | 425 | 46.10% | 117 |
| 0.5 | 717 | 335 | 46.72% | 84 |
| 0.8 | 174 | 80 | 45.98% | 20 |

## Distribution By Volume

| Volume | Labels | HDV takes priority | Ratio | Strict non-yield |
| --- | ---: | ---: | ---: | ---: |
| low | 612 | 277 | 45.26% | 63 |
| medium | 649 | 298 | 45.92% | 97 |
| high | 552 | 265 | 48.01% | 61 |

## Interpretation

The stress batch shows that the data pipeline is suitable for the first prediction model if the primary target is:

```text
hdv_takes_priority = 1 if the HDV enters the conflict zone before the interacting vehicle by a time margin.
```

This target is balanced and decision-relevant. It predicts whether a CAV should assume the HDV will claim the conflict-zone priority.

The stricter label:

```text
strict_non_yield = 1 if the HDV enters first and does not strongly decelerate before the conflict zone.
```

is too sparse for the first prediction target, but it remains useful as an auxiliary risk label and for failure-case analysis.

## Decision

Use `hdv_takes_priority` as the primary supervised prediction label for the first GRU/graph model. Keep `strict_non_yield` in the label file as an auxiliary safety-risk indicator.

## Next Step

Build the prediction dataset generator:

```text
vehicle history windows + interaction edge features + hdv_takes_priority labels
```

Then train and compare:

1. constant-arrival rule;
2. logistic/SVM baseline;
3. GRU-only;
4. GRU + graph attention.

