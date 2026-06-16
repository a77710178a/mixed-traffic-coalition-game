# Safety Metrics Pilot

Date: 2026-06-17

Remote directory:

```text
/public/home/xiaohei_0/hx/my_paper01/sim/prototype
```

Implemented module:

```text
src/safety_metrics.py
```

## What Was Added

The closed-loop SUMO runner now computes conflict-zone safety metrics after each simulation:

```text
conflict-zone occupancies
PET
mean PET
minimum entry-time gap
near-conflict count under a PET threshold
```

Outputs are written under each closed-loop log directory:

```text
conflict_zone_occupancies.csv
safety_metrics.json
```

The per-run closed-loop summary now includes:

```text
occupancy_count
conflict_pair_count
near_conflict_count
min_pet_s
mean_pet_s
min_entry_gap_s
safety_metrics
conflict_zone_occupancies
```

## Definition Used In This Pilot

For each vehicle, conflict-zone occupancy is extracted from `distance_to_center <= zone_radius_m`.

```text
entry_time = first time inside the conflict zone
exit_time = first time outside the conflict zone after being inside
PET = later entry time - earlier exit time
near conflict = PET <= near_conflict_pet_s
```

Pairs from the same origin are excluded. Pairs from different origins are currently treated as possible conflicts.

## Verification

Local tests:

```text
python -m unittest sim/prototype/tests/test_safety_metrics.py sim/prototype/tests/test_allocation_policy.py
13 tests OK
```

Server tests:

```text
conda run -n sumoenv python -m unittest sim/prototype/tests/test_safety_metrics.py sim/prototype/tests/test_allocation_policy.py
13 tests OK
```

Server smoke-test command:

```bash
conda run -n sumoenv python src/run_closed_loop_allocation.py \
  --config config/stress_scenario.json \
  --seed 9 \
  --volume low \
  --penetration 0.5 \
  --duration 60 \
  --method prediction_coalition \
  --max-release-count 3 \
  --safe-arrival-gap-s 1.2 \
  --near-conflict-pet-s 1.5
```

Observed safety fields from the smoke test:

| Method | Throughput | Near-conflict count ↓ | Min PET ↑ | Mean PET ↑ | Min entry gap ↑ |
| --- | ---: | ---: | ---: | ---: | ---: |
| FCFS | 3 | 23 | -33.40 | -3.0143 | 0.10 |
| prediction_coalition | 2 | 33 | -45.10 | -8.3898 | 0.20 |

## Interpretation

The safety metric pipeline is now operational and automatically linked to the closed-loop runner. This makes the simulator more useful for transportation-journal evidence because it no longer relies only on throughput, travel time, and waiting-time metrics.

However, the current PET values are not yet final paper-grade safety evidence. The broad center-zone definition and broad "different origin = possible conflict" rule can over-count conflicts and produce strongly negative PET values when vehicles queue or overlap inside the center region. This is acceptable for development diagnostics, but formal experiments need a sharper conflict-pair definition.

## Next Step

Improve conflict safety semantics:

```text
1. Define movement-level conflict pairs instead of all different-origin pairs.
2. Optionally split the center into finer conflict zones for left/through/right movements.
3. Report PET only for movement pairs that geometrically conflict.
4. Keep near-conflict count as an explicit safety metric in every batch table.
```

This should happen before large-scale formal experiments or fairness/efficiency claims.
