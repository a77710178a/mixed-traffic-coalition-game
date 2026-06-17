# SUMO Prototype

This directory contains the first runnable prototype for the paper:

**Interaction-Aware Deep Prediction and Fair Coalition Allocation for Mixed Traffic at Unsignalized Intersections**

The prototype is intentionally small. It generates an unsignalized intersection, creates mixed CAV/HDV traffic, records TraCI vehicle states, extracts conflict-zone events, and derives HDV yield/non-yield labels. The four-leg layout remains as the debugging baseline; the T-junction layout is the main geometry for formal experiments.

## Remote Runtime

Use the server environment:

```bash
conda activate sumoenv
```

or run scripts through:

```bash
/public/home/xiaohei_0/conda38/bin/conda run -n sumoenv python ...
```

## Quick Smoke Test

```bash
cd /public/home/xiaohei_0/hx/my_paper01/sim/prototype
python src/generate_network.py --config config/default_scenario.json
python src/generate_routes.py --config config/default_scenario.json --seed 1 --volume low --penetration 0.5 --duration 120
python src/run_sumo.py --config config/default_scenario.json --seed 1 --volume low --penetration 0.5 --duration 120
python src/extract_conflict_events.py --config config/default_scenario.json --run-id seed1_low_pen50
python src/generate_yield_labels.py --config config/default_scenario.json --run-id seed1_low_pen50
python src/build_prediction_dataset.py --run-id seed1_low_pen50 --high-confidence-only
```

Outputs are written under `logs/`, `labels/`, and `reports/`.

Prediction datasets are written under `datasets/<run_id>/` as JSONL files. Each sample contains the HDV history, interacting-vehicle history, edge features, and the primary `hdv_takes_priority` label.

## T-Junction Scenario

The main paper scenario is a north-south main road with an east-side branch:

```bash
python src/generate_network.py --config config/t_junction_scenario.json
python src/generate_routes.py --config config/t_junction_scenario.json --seed 1 --volume low --penetration 0.5 --duration 60
python src/run_sumo.py --config config/t_junction_scenario.json --seed 1 --volume low --penetration 0.5 --duration 60
python src/render_network_preview.py \
  --config config/t_junction_scenario.json \
  --output reports/t_junction_network_preview.svg
```

T-junction runs use a scenario-prefixed run id such as `t_junction_unsignalized_stress_p0_seed1_low_pen50`, so they can coexist with the original four-leg debug runs.

## Prediction Baselines

After building a merged prediction dataset, run:

```bash
python src/train_prediction_baselines.py \
  --dataset datasets/stress_seed5_6_priority_hc/prediction_samples.jsonl \
  --train-seeds 5 \
  --test-seeds 6
```

This evaluates the constant-arrival rule and a lightweight logistic-regression baseline.

For the GRU-only temporal predictor, run:

```bash
python src/train_gru_predictor.py \
  --dataset datasets/stress_seed5_6_priority_hc_h3/prediction_samples.jsonl \
  --train-seeds 5 \
  --test-seeds 6
```

For the GRU + edge-feature predictor, run:

```bash
python src/train_gru_edge_predictor.py \
  --dataset datasets/stress_seed5_6_priority_hc_h3/prediction_samples.jsonl \
  --train-seeds 5 \
  --test-seeds 6
```

## Closed-Loop Allocation Pilot

Run one closed-loop allocation method through SUMO:

```bash
python src/run_closed_loop_allocation.py \
  --config config/stress_scenario.json \
  --seed 7 \
  --volume low \
  --penetration 0.5 \
  --duration 90 \
  --method fcfs
```

Run a small comparison batch:

```bash
python src/run_closed_loop_batch.py \
  --config config/stress_scenario.json \
  --seeds 7,8 \
  --volumes low,medium \
  --penetrations 0.5 \
  --methods fcfs,prediction_fcfs,prediction_coalition \
  --duration 90 \
  --max-release-count 3 \
  --safe-arrival-gap-s 1.2 \
  --output-name closed_loop_pilot_seed7_8_low_medium_pen50_d90
```

The current closed-loop policy is a development baseline. It controls CAVs only, observes HDVs, and writes per-run summaries plus aggregate CSV files under `reports/`.

`prediction_coalition` forms a small release set rather than always releasing a single vehicle. The main knobs are `--max-release-count`, `--safe-arrival-gap-s`, and `--fairness-weight`.

To use the logistic learned-priority predictor in closed loop, pass a baseline summary:

```bash
python src/run_closed_loop_batch.py \
  --config config/stress_scenario.json \
  --seeds 9,10 \
  --volumes low,medium \
  --penetrations 0.5 \
  --methods fcfs,prediction_coalition \
  --duration 90 \
  --priority-model reports/baseline_seed5_train_seed6_test_h3/prediction_baseline_summary.json \
  --output-name prototype_validation_logistic_seed9_10_low_medium_pen50_d90
```

Closed-loop runs also compute conflict-zone safety metrics:

```text
PET
mean PET
minimum entry-time gap
near-conflict count
```

The current safety metric implementation uses movement-level conflict-pair filtering, but the conflict zone is still represented by a simplified center radius. Treat PET outputs as development diagnostics until finer conflict zones are added.
