# Prediction Baseline Results

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

Important integrity note:

The first 1-second prediction run gave near-perfect logistic regression results. That run was not used as the main result because the prediction horizon was too close to the conflict event. The feature `entry_time_diff_other_minus_hdv` was also removed from the logistic baseline because it is a post-event label-derived field and would leak future information.

## Main Baseline Table

| Method | Accuracy | Precision | Recall | F1 | AUC | TP | TN | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Constant-arrival rule | 0.8849 | 0.8851 | 0.8750 | 0.8800 | 0.9330 | 308 | 338 | 40 | 44 |
| Constant-arrival rule, 3 s horizon | 0.8371 | 0.8288 | 0.8320 | 0.8304 | 0.8180 | 213 | 234 | 44 | 43 |
| Logistic regression, 3 s horizon | 0.9551 | 0.9496 | 0.9570 | 0.9533 | 0.9884 | 245 | 265 | 13 | 11 |

## Interpretation

The constant-arrival rule is already strong because the label is based on conflict-zone priority. This is useful: it gives the paper a meaningful, interpretable baseline rather than an artificially weak comparison.

The 3-second-horizon logistic baseline improves substantially over constant arrival using current state and edge features. This supports the value of learned interaction features, but it is still a shallow baseline. The next model should test whether temporal history improves over the single-time-step logistic baseline.

## Next Step

Train the GRU-only predictor on the same 3-second-horizon dataset. The next key comparison is:

```text
GRU-only vs. logistic regression
```

After that, add edge/graph attention:

```text
GRU + edge attention vs. GRU-only
```

