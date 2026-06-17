# Prototype Validation Report

Date: 2026-06-17

Remote directory:

```text
/public/home/xiaohei_0/hx/my_paper01/sim/prototype
```

## Validation Scope

This report closes the current stage:

```text
method prototype validation + mechanism debugging platform
```

The goal is not to claim final paper results. The goal is to verify that the platform can support formal experiments after one more round of scenario-scale expansion and metric refinement.

## Completed Capabilities

| Component | Status | Evidence |
| --- | --- | --- |
| SUMO four-leg unsignalized intersection | done | network/route generation and remote smoke tests |
| Mixed CAV/HDV demand generation | done | stress scenario with CAV penetration and HDV profiles |
| Conflict event and HDV priority labels | done | high-confidence priority datasets |
| Prediction baselines | done | constant-arrival, logistic regression, GRU-only, GRU+edge, graph attention |
| Closed-loop TraCI control | done | CAV hold/release commands in SUMO |
| Coalition release-set policy | done | `max_release_count`, `safe_arrival_gap_s`, HDV risk, fairness credit |
| Batch runner | done | per-run CSV and aggregate CSV outputs |
| Safety metrics | done, development-grade | movement-level PET / near-conflict / entry-gap metrics |
| Learned predictor hook | done | logistic baseline summary can drive closed-loop HDV priority probability |
| Regression tests | done | 18 Python unit tests on policy, predictor, and safety metrics |

## Validation Commands

Server unit tests:

```bash
conda run -n sumoenv python -m unittest \
  sim/prototype/tests/test_safety_metrics.py \
  sim/prototype/tests/test_priority_predictor.py \
  sim/prototype/tests/test_allocation_policy.py
```

Result:

```text
18 tests OK
```

Heuristic-priority closed-loop validation:

```bash
conda run -n sumoenv python src/run_closed_loop_batch.py \
  --config config/stress_scenario.json \
  --seeds 9,10 \
  --volumes low,medium \
  --penetrations 0.5 \
  --methods fcfs,prediction_coalition \
  --duration 90 \
  --control-radius-m 45 \
  --fairness-weight 0.15 \
  --max-release-count 3 \
  --safe-arrival-gap-s 1.2 \
  --near-conflict-pet-s 1.5 \
  --output-name prototype_validation_heuristic_seed9_10_low_medium_pen50_d90
```

Learned-logistic-priority closed-loop validation:

```bash
conda run -n sumoenv python src/run_closed_loop_batch.py \
  --config config/stress_scenario.json \
  --seeds 9,10 \
  --volumes low,medium \
  --penetrations 0.5 \
  --methods fcfs,prediction_coalition \
  --duration 90 \
  --control-radius-m 45 \
  --fairness-weight 0.15 \
  --max-release-count 3 \
  --safe-arrival-gap-s 1.2 \
  --near-conflict-pet-s 1.5 \
  --priority-model reports/baseline_seed5_train_seed6_test_h3/prediction_baseline_summary.json \
  --output-name prototype_validation_logistic_seed9_10_low_medium_pen50_d90
```

## Sanity Results

These are development-stage sanity results, not final manuscript numbers.

### Heuristic Priority

| Method | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Stop proxy ↓ | Waiting Gini ↓ | Near conflicts ↓ | Mean PET ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 4 | 5.50 | 45.5380 | 19.2751 | 36.75 | 0.5497 | 5.25 | -25.7487 |
| prediction_coalition | 4 | 9.75 | 42.5452 | 19.7155 | 35.50 | 0.5923 | 6.75 | -20.3867 |

### Logistic Learned Priority

| Method | Runs | Throughput ↑ | Mean travel time ↓ | Mean max wait ↓ | Stop proxy ↓ | Waiting Gini ↓ | Near conflicts ↓ | Mean PET ↑ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FCFS | 4 | 5.50 | 45.5380 | 19.2751 | 36.75 | 0.5497 | 5.25 | -25.7487 |
| prediction_coalition | 4 | 7.75 | 43.1623 | 21.5534 | 35.00 | 0.5660 | 5.50 | -29.2158 |

## Interpretation

The platform is now complete enough for method debugging:

```text
traffic generation -> HDV priority prediction -> coalition allocation -> closed-loop SUMO control -> efficiency/fairness/safety metrics -> batch summaries
```

The coalition mechanism shows a consistent efficiency signal in these sanity runs:

```text
throughput improves
mean observed travel time decreases
```

The fairness and safety results are not yet strong:

```text
waiting-time inequality can increase
near-conflict count may increase or only slightly improve
PET values remain sensitive to zone definition and queueing behavior
```

The learned logistic predictor hook works and closes the "learning + allocation" loop, but the current online feature construction is approximate because it uses candidate states rather than the full offline pairwise history used during baseline training.

## What Can Be Claimed Now

Safe claims for internal progress:

```text
The full prototype platform is operational.
The method can be evaluated in closed-loop SUMO.
The platform reports efficiency, fairness, and safety diagnostics.
A learned-priority predictor can be connected to coalition allocation.
Coalition release-set control can improve throughput/travel time in small sanity scenarios.
```

Claims not yet safe for a paper:

```text
The proposed method is safer than FCFS.
The fairness term reduces waiting inequality.
The learned predictor is superior in closed-loop control.
The current PET values are final safety evidence.
The result generalizes across demand, penetration, HDV behavior, and seeds.
```

## Remaining Work Before Formal Experiments

The prototype stage can be considered closed. The next stage should be formal experiment design and expansion:

```text
1. Use movement-level PET as default, but refine conflict zones if PET remains too negative.
2. Expand to 5-10 seeds, low/medium/high volumes, and 20/50/80% CAV penetration.
3. Add ablations: no fairness, no learned predictor, no risk constraint, max coalition size.
4. Improve online learned features or train an online-compatible predictor.
5. Report mean/std across seeds rather than single aggregate means.
```

## Go / No-Go

Prototype validation platform:

```text
GO
```

Formal paper experiment conclusions:

```text
NO-GO until expanded experiments and stronger safety/fairness evidence are available.
```

## T-Junction Route-Zone Geometry Smoke Test

Date: 2026-06-17

Configuration: `sim/prototype/config/t_junction_scenario.json`

Checks:

- Unit tests: `37` tests passed for route geometry, route-zone events, route-zone graph neighbors, T-junction topology, safety metrics, priority predictor, and allocation policy.
- SUMO smoke run: generated `5581` vehicle-state rows and used `geometry_mode=route_zones`.
- Route-zone event extraction: generated `24` vehicle-zone occupancy events.
- Yield-label generation: generated `6` labels, all high-confidence in this smoke run.
- Closed-loop smoke run: generated `6804` state rows, `517` allocation-decision rows, and route-zone safety outputs.

Observed route-zone counts:

- `event_count`: 24
- `label_count`: 6
- `closed_loop_occupancy_count`: 10
- `closed_loop_conflict_pair_count`: 0
- `closed_loop_near_conflict_count`: 0

Implementation note:

SUMO's generated network applies a `netOffset`, so route-zone extraction now normalizes vehicle coordinates by the recorded junction center in `run_meta.json` before testing zone occupancy.
