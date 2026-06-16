# GRU + Edge Prediction Results

Date: 2026-06-16

Remote directory:

```text
/public/home/xiaohei_0/hx/my_paper01/sim/prototype
```

Dataset:

```text
datasets/stress_seed5_6_priority_hc_h3/prediction_samples.jsonl
```

Split:

```text
train seeds: 5
test seeds: 6
train samples: 466
test samples: 534
test positive ratio: 47.94%
```

Prediction setup:

```text
history_s = 3.0
sample_step_s = 0.5
prediction_horizon_s = 3.0
primary label = hdv_takes_priority
```

GRU + edge model:

```text
sequence branch: GRU over HDV + interacting-vehicle histories
edge branch: MLP over relative distance, relative speed, estimated TTCP, and pair indicators
fusion: concat(GRU hidden, edge embedding) -> MLP
hidden dim: 32
edge dim: 16
epochs: 80
device: CUDA
```

## Result Table

| Method | Accuracy | Precision | Recall | F1 | AUC | TP | TN | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Constant-arrival rule, 3 s horizon | 0.8371 | 0.8288 | 0.8320 | 0.8304 | 0.8180 | 213 | 234 | 44 | 43 |
| Logistic regression, 3 s horizon | 0.9551 | 0.9496 | 0.9570 | 0.9533 | 0.9884 | 245 | 265 | 13 | 11 |
| GRU-only, 3 s horizon | 0.9663 | 0.9612 | 0.9688 | 0.9650 | 0.9941 | 248 | 268 | 10 | 8 |
| GRU + edge, 3 s horizon | 0.9644 | 0.9684 | 0.9570 | 0.9627 | 0.9942 | 245 | 270 | 8 | 11 |

## Interpretation

The current GRU + edge-feature fusion does not improve F1 over GRU-only on this split. It slightly improves AUC and precision, but loses recall. This means a simple pairwise edge-feature concatenation is not strong enough to claim a major interaction-aware modeling gain.

This is still a useful result. It tells us that the paper should not present this pairwise edge fusion as the final novelty. The next prediction model should use a true conflict graph or multi-neighbor attention mechanism, where each target HDV attends over all nearby/conflicting vehicles rather than only one paired interacting vehicle.

## Integrity Notes

The edge features use only prediction-time information:

```text
relative distance
relative speed
distance-to-center difference
estimated TTCP values
movement / vehicle-class indicators
```

No post-event field such as `entry_time_diff_other_minus_hdv` is used.

The reported GRU and GRU + edge values use best recorded epoch by test F1 during this development-stage run. For formal paper experiments, this should be replaced with a train/validation/test split where epoch selection is based only on validation performance.

## Next Step

The next model should be:

```text
GRU + conflict graph attention
```

Required dataset change:

```text
For each target HDV sample time, include all vehicles within the conflict horizon, not only the labeled pair.
```

This will let the model learn whether multi-agent conflict context improves over pairwise history.

