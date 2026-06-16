# SUMO Prototype

This directory contains the first runnable prototype for the paper:

**Interaction-Aware Deep Prediction and Fair Coalition Allocation for Mixed Traffic at Unsignalized Intersections**

The prototype is intentionally small. It generates a four-leg unsignalized intersection, creates mixed CAV/HDV traffic, records TraCI vehicle states, extracts conflict-zone events, and derives HDV yield/non-yield labels.

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
