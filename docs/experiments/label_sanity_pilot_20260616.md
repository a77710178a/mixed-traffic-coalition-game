# Label Sanity Pilot

Date: 2026-06-16

Remote directory:

```text
/public/home/xiaohei_0/hx/my_paper01/sim/prototype
```

Runner:

```text
sim/prototype/src/run_label_sanity_batch.py
```

Command:

```bash
python src/run_label_sanity_batch.py \
  --config config/default_scenario.json \
  --seeds 4 \
  --volumes low,medium,high \
  --penetrations 0.5 \
  --duration 120
```

## Aggregate Result

| Runs | Vehicles | Conflict events | Labels | Non-yield | Yield | Non-yield ratio | High confidence | Low confidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 203 | 124 | 150 | 16 | 134 | 10.67% | 128 | 22 |

## Per-Run Result

| Run ID | Volume | Vehicles | State rows | Events | HDV events | CAV events | Labels | Non-yield | Yield |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| seed4_low_pen50 | low | 39 | 8402 | 32 | 13 | 19 | 26 | 1 | 25 |
| seed4_medium_pen50 | medium | 73 | 27994 | 44 | 22 | 22 | 57 | 3 | 54 |
| seed4_high_pen50 | high | 91 | 40272 | 48 | 28 | 20 | 67 | 12 | 55 |

## Interpretation

The pipeline is working: it generates mixed traffic, conflict events, and labels without manual intervention. However, the label distribution is yield-heavy. This is likely caused by conservative SUMO priority/gap behavior and by the current non-yield rule requiring both earlier entry and no strong pre-zone deceleration.

This is a data-design issue rather than a pipeline failure. Before training the GRU/graph predictor, the next step should increase scenario pressure and inspect label rules.

## Next Adjustments

1. Increase aggressive HDV share from `0.25` to `0.50-0.70` in a stress configuration.
2. Test longer duration, at least `300 s`, to reduce small-sample noise.
3. Add penetration values `0.2` and `0.8` to see whether HDV-CAV interaction density changes.
4. Compare label thresholds:
   - `epsilon_t_s = 0.3 / 0.5 / 0.8`
   - `yield_decel_mps2 = 1.0 / 1.5 / 2.0`
5. Add a manual sample audit of 10 high-confidence yield and 10 high-confidence non-yield cases.

