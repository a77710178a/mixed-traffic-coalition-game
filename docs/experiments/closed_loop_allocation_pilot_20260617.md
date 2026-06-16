# Closed-Loop Allocation Pilot

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
  --output-name closed_loop_pilot_seed7_8_low_medium_pen50_d90
```

Outputs:

```text
reports/closed_loop_pilot_seed7_8_low_medium_pen50_d90/closed_loop_batch_runs.csv
reports/closed_loop_pilot_seed7_8_low_medium_pen50_d90/closed_loop_batch_aggregate.csv
reports/closed_loop_pilot_seed7_8_low_medium_pen50_d90/closed_loop_batch_summary.json
```

## Implemented Methods

| Method | Current behavior |
| --- | --- |
| FCFS | Estimates arrival time to the intersection center and releases the earliest candidate. Other controlled CAVs inside the control radius are held at a low speed. |
| prediction_fcfs | Uses the same release rule as FCFS, with the same current behavior in this pilot. |
| prediction_coalition | Adds a simple HDV priority/risk bonus and a waiting-time fairness credit before sorting release order. |

Important scope note:

```text
Only CAVs are directly controlled through TraCI speed commands. HDVs are observed but not directly controlled.
```

## Aggregate Results

These are development-stage pilot results, not paper-ready final numbers.

| Method | Runs | Throughput ↑ | Mean observed travel time ↓ | Mean max waiting time ↓ | Stop proxy ↓ | Waiting Gini ↓ | Min pairwise TTC proxy ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 4 | 7.00 | 43.4591 | 18.9184 | 34.75 | 0.5546 | 0.00119 |
| prediction_fcfs | 4 | 7.00 | 43.4591 | 18.9184 | 34.75 | 0.5546 | 0.00119 |
| prediction_coalition | 4 | 6.50 | 43.8449 | 18.8603 | 35.00 | 0.5563 | 0.00140 |

## Interpretation

The closed-loop pipeline is now operational: SUMO runs, TraCI collects vehicle states, the allocation policy generates release/hold decisions, CAV speed commands are applied, and per-run plus aggregate metrics are written.

The current allocation rule is intentionally simple and too conservative. It releases only the first vehicle in the ordering and holds other CAVs inside the control radius. This creates a useful baseline implementation, but it is not yet a strong proposed method. The pilot confirms that the current `prediction_coalition` variant does not improve throughput or fairness over FCFS.

## Scientific Implication

This is a good integrity checkpoint. We should not claim the coalition method is effective from this pilot. Instead, the next implementation step should make the coalition mechanism more meaningful:

```text
form a compatible release set instead of releasing only one vehicle
```

The next policy should decide a small passing coalition using:

```text
estimated arrival time
HDV priority/risk probability
movement compatibility
waiting-time fairness credit
maximum coalition size
```

## Next Step

Implement a less conservative coalition release policy:

```text
1. Keep the first selected vehicle.
2. Add additional CAVs only when they are low-risk and not in near-simultaneous conflict.
3. Penalize vehicles with high predicted HDV priority conflict.
4. Use waiting-time fairness to prevent starvation.
```

Then rerun the same pilot and compare against this checkpoint.
