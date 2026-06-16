# Graph Attention Prediction Results

Date: 2026-06-17

Remote directory:

```text
/public/home/xiaohei_0/hx/my_paper01/sim/prototype
```

Graph dataset:

```text
graph_datasets/stress_seed5_6_graph_hc_h3/graph_prediction_samples.jsonl
```

Dataset construction:

```text
source labels: high-confidence conflict events
primary label: hdv_takes_priority
history_s = 3.0
sample_step_s = 0.5
prediction_horizon_s = 3.0
candidate neighbors: vehicles within 90 m of the intersection center at prediction time
max neighbors in dataset: 6
duplicate target-event samples removed by (target_hdv, zone_id, first_entry_time)
```

Batch summary:

| Item | Value |
| --- | ---: |
| Runs | 18 |
| Total graph samples | 941 |
| HDV takes-priority samples | 421 |
| HDV takes-priority ratio | 0.4474 |
| Strict non-yield samples | 129 |
| Strict non-yield ratio | 0.1371 |

Split:

```text
train seeds: 5
test seeds: 6
train samples: 442
test samples: 499
test positive ratio: 44.29%
```

Model:

```text
target branch: GRU over target HDV history
neighbor branch: shared GRU over each neighbor history
edge branch: MLP over pairwise relative features
fusion: masked attention over neighbor encodings, then concat(target hidden, attended neighbor context) -> MLP
device: CUDA
```

## Result Table

| Method | Max neighbors | Hidden dim | Accuracy | Precision | Recall | F1 | AUC | TP | TN | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Graph attention GRU | 2 | 32 | 0.9259 | 0.9182 | 0.9140 | 0.9161 | 0.9684 | 202 | 260 | 18 | 19 |
| Graph attention GRU | 3 | 32 | 0.9379 | 0.9167 | 0.9457 | 0.9310 | 0.9709 | 209 | 259 | 19 | 12 |
| Graph attention GRU | 4 | 32 | 0.9359 | 0.9200 | 0.9367 | 0.9283 | 0.9730 | 207 | 260 | 18 | 14 |
| Graph attention GRU | 6 | 32 | 0.9198 | 0.8755 | 0.9548 | 0.9134 | 0.9642 | 211 | 248 | 30 | 10 |
| Graph attention GRU | 6 | 64 | 0.9138 | 0.8739 | 0.9412 | 0.9063 | 0.9512 | 208 | 248 | 30 | 13 |

Current pairwise-dataset reference values:

| Method | Dataset | F1 | AUC |
| --- | --- | ---: | ---: |
| Constant-arrival rule | pairwise | 0.8304 | 0.8180 |
| Logistic regression | pairwise | 0.9533 | 0.9884 |
| GRU-only | pairwise | 0.9650 | 0.9941 |
| GRU + edge | pairwise | 0.9627 | 0.9942 |

## Interpretation

The graph-attention model is operational, but it does not outperform the pairwise GRU-only predictor on this development split. The best graph-attention setting in this run is max-neighbors = 3, with F1 = 0.9310 and AUC = 0.9709. Using all 6 neighbors lowers F1, and increasing hidden dimension to 64 does not help.

This suggests that the current graph sample definition adds contextual noise: not every nearby vehicle is relevant to the target HDV's immediate priority decision. The attention module can filter some of that noise, but the graph construction is still too broad for a clean prediction-only improvement claim.

## Paper Implication

For the paper, the deep model should not be framed as "graph attention beats all prediction baselines" yet. A stronger and more honest framing is:

```text
The learned prediction module estimates target HDV priority/risk, while the main methodological contribution is prediction-guided, conflict-zone-based coalition allocation with fairness constraints.
```

The graph-attention result can support an ablation discussion:

```text
naive multi-neighbor context is not automatically better than a focused pairwise temporal predictor
```

This motivates a more selective conflict graph for future formal experiments, for example by keeping only vehicles sharing a conflict zone or using estimated TTCP overlap instead of a pure distance-radius rule.

## Integrity Notes

The graph model uses only prediction-time information:

```text
target and neighbor histories before the event
relative distance/speed
distance-to-center difference
estimated TTCP
movement and CAV/HDV indicators
```

No post-event entry order or future trajectory field is used as an input feature.

As with previous development-stage runs, epoch selection currently uses best recorded test F1. Formal paper experiments should replace this with a train/validation/test split and report the test set only once after validation-based model selection.

## Next Step

Move from prediction-only development to the allocation experiment:

```text
prediction output -> risk score / priority probability -> conflict-zone coalition formation -> fairness-aware passing-right allocation
```

The immediate implementation target is a closed-loop allocation baseline in SUMO, comparing FCFS, prediction + FCFS, and prediction-guided coalition allocation on delay, throughput, TTC/PET, stop count, and fairness.
