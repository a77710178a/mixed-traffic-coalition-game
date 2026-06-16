# Closed-Loop Coalition V2 Pilot

Date: 2026-06-17

Remote directory:

```text
/public/home/xiaohei_0/hx/my_paper01/sim/prototype
```

Pilot command:

```bash
conda run -n sumoenv python src/run_closed_loop_batch.py \
  --config config/stress_scenario.json \
  --seeds 7,8 \
  --volumes low,medium \
  --penetrations 0.5 \
  --methods fcfs,prediction_fcfs,prediction_coalition \
  --duration 90 \
  --control-radius-m 45 \
  --fairness-weight 0.15 \
  --max-release-count 3 \
  --safe-arrival-gap-s 1.2 \
  --output-name closed_loop_pilot_coalition_v2_seed7_8_low_medium_pen50_d90
```

## Policy Change

The previous pilot released only the first vehicle in the sorted order. Coalition V2 changes `prediction_coalition` into a small release-set policy:

```text
1. Sort candidates by arrival time, HDV priority/risk, and fairness credit.
2. Select up to max_release_count vehicles.
3. Reject a candidate if its estimated arrival time is too close to an already selected vehicle.
4. Reject a CAV if it has a near-simultaneous high-priority HDV conflict.
5. Release selected CAVs and hold non-selected CAVs.
```

Only CAVs are directly controlled. HDVs are observed and can influence the release set, but their speed is not commanded.

## Aggregate Results

These are development-stage pilot results, not paper-ready final numbers.

| Method | Runs | Throughput ↑ | Mean observed travel time ↓ | Mean max waiting time ↓ | Stop proxy ↓ | Waiting Gini ↓ | Min pairwise TTC proxy ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 4 | 7.00 | 43.4591 | 18.9184 | 34.75 | 0.5546 | 0.00119 |
| prediction_fcfs | 4 | 7.00 | 43.4591 | 18.9184 | 34.75 | 0.5546 | 0.00119 |
| prediction_coalition V2 | 4 | 8.00 | 41.9498 | 20.1584 | 37.00 | 0.5615 | 0.00166 |

Compared with the previous conservative coalition pilot:

| Method | Throughput ↑ | Mean observed travel time ↓ | Mean max waiting time ↓ | Waiting Gini ↓ |
| --- | ---: | ---: | ---: | ---: |
| prediction_coalition V1 | 6.50 | 43.8449 | 18.8603 | 0.5563 |
| prediction_coalition V2 | 8.00 | 41.9498 | 20.1584 | 0.5615 |

## Interpretation

Coalition V2 produces the first useful positive signal for the closed-loop method. It improves average throughput and reduces observed travel time relative to FCFS on this small pilot:

```text
throughput: 7.00 -> 8.00
mean observed travel time: 43.4591 s -> 41.9498 s
```

However, the improvement has a cost:

```text
mean max waiting time increases
stop proxy increases
waiting-time Gini slightly increases
```

This suggests the current coalition rule is more efficient but not yet fairness-optimal. The result supports the paper's mechanism direction, but the fairness term needs a stronger or better-normalized role before we can claim fairness improvement.

## Per-Run Notes

The V2 coalition improved or matched throughput in all four pilot scenarios:

| Seed | Volume | FCFS throughput | Coalition V2 throughput | FCFS travel time | Coalition V2 travel time |
| ---: | --- | ---: | ---: | ---: | ---: |
| 7 | low | 8 | 8 | 39.2711 | 38.5200 |
| 7 | medium | 7 | 8 | 48.1547 | 46.1203 |
| 8 | low | 5 | 6 | 42.8956 | 42.0067 |
| 8 | medium | 8 | 10 | 43.5149 | 41.1522 |

## Integrity Notes

The positive result is still a pilot:

```text
seeds: 2
volumes: low, medium
CAV penetration: 50%
duration: 90 s
single four-leg unsignalized intersection
proxy TTC metric based on estimated arrival-time gaps
```

Formal experiments must use more seeds, more penetration rates, longer durations, and stronger safety metrics such as post-encroachment time from conflict-zone entry/exit logs.

## Next Step

Run an ablation sweep over:

```text
max_release_count: 1, 2, 3
safe_arrival_gap_s: 0.8, 1.2, 1.6
fairness_weight: 0.0, 0.15, 0.3, 0.5
```

The goal is to find a regime where efficiency improves without increasing waiting inequality too much.
