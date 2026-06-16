# Prediction Dataset Build

Date: 2026-06-16

Remote directory:

```text
/public/home/xiaohei_0/hx/my_paper01/sim/prototype
```

Dataset builder:

```text
sim/prototype/src/build_prediction_dataset.py
sim/prototype/src/build_prediction_dataset_batch.py
```

## Dataset Definition

Each JSONL sample contains:

```text
target HDV id
interacting vehicle id
sample time
HDV history window
interacting vehicle history window
edge features
primary label: hdv_takes_priority
auxiliary label: strict_non_yield
```

Window settings:

```text
history_s = 3.0
sample_step_s = 0.5
prediction_horizon_s = 1.0
high_confidence_only = true
```

This gives 7 history points per vehicle:

```text
t-3.0, t-2.5, t-2.0, t-1.5, t-1.0, t-0.5, t
```

## Pilot Single-Run Check

Run:

```text
seed5_medium_pen50
```

Result:

```text
input labels: 107
written samples: 77
skipped low-confidence labels: 18
skipped incomplete-history labels: 12
hdv_takes_priority positives: 38
strict_non_yield positives: 12
```

The sample format was verified to contain both vehicle histories, edge features, context fields, and labels.

## Batch Dataset

Batch:

```text
seeds: 5, 6
volumes: low, medium, high
CAV penetration: 0.2, 0.5, 0.8
total runs: 18
```

Remote output:

```text
/public/home/xiaohei_0/hx/my_paper01/sim/prototype/datasets/stress_seed5_6_priority_hc/prediction_samples.jsonl
```

Summary:

| Runs | Samples | HDV takes priority | Ratio | Strict non-yield | Ratio |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 18 | 1366 | 666 | 48.76% | 176 | 12.88% |

## Interpretation

The prediction dataset is ready for the first supervised baselines. The primary label is close to balanced after filtering to high-confidence interactions, which makes it suitable for logistic/SVM, GRU-only, and GRU+graph comparison.

The strict non-yield label remains sparse and should be treated as an auxiliary risk signal or failure-analysis label, not as the main first-stage supervised target.

## Next Step

Implement first prediction baselines:

```text
constant-arrival rule
logistic regression or SVM with edge features
GRU-only temporal model
GRU + graph/edge attention model
```

