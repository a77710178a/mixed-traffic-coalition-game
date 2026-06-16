# GRU Prediction Results

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

GRU-only model:

```text
input: HDV history + interacting-vehicle history
sequence length: 7
input dim: 12
hidden dim: 32
layers: 1
epochs: 80
device: CUDA
```

## Result Table

| Method | Accuracy | Precision | Recall | F1 | AUC | TP | TN | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Constant-arrival rule, 3 s horizon | 0.8371 | 0.8288 | 0.8320 | 0.8304 | 0.8180 | 213 | 234 | 44 | 43 |
| Logistic regression, 3 s horizon | 0.9551 | 0.9496 | 0.9570 | 0.9533 | 0.9884 | 245 | 265 | 13 | 11 |
| GRU-only, 3 s horizon | 0.9663 | 0.9612 | 0.9688 | 0.9650 | 0.9941 | 248 | 268 | 10 | 8 |

## Interpretation

GRU-only improves over logistic regression on the current split. The gain is modest, which means the current problem is still largely explainable by near-conflict kinematic features. This is useful evidence, not a problem: it tells us that the next claimed contribution should not be "GRU alone is dramatically better."

The next meaningful test is whether an interaction-aware graph or edge-attention module can improve over GRU-only, especially under harder splits or longer prediction horizons.

## Integrity Notes

The GRU-only input does not include post-event fields such as `entry_time_diff_other_minus_hdv`. It uses only historical states before the prediction time.

The dataset is still generated from SUMO. These results support the internal prediction pipeline, but they do not yet show external validity on real trajectory data.

## Next Step

Implement an edge-aware temporal model:

```text
GRU encodes HDV and interacting-vehicle histories
edge features encode relative distance, speed, and estimated TTCP
MLP/attention head predicts hdv_takes_priority
```

The key comparison will be:

```text
GRU + edge features vs. GRU-only
```
