# SUMO Prototype Plan

Date: 2026-06-16

Purpose: define the minimum SUMO prototype needed to generate data, train the first prediction model, and test fairness-aware coalition allocation. This plan does not contain experimental results.

## 1. Prototype Goal

The prototype should answer two early questions:

1. Can we generate reliable `yield / non-yield` labels from mixed-traffic interactions at an unsignalized intersection?
2. Can predicted non-yielding risk be used by a fairness-regularized coalition allocator to improve safety/fairness trade-offs compared with simple baselines?

The prototype should be intentionally small. It should generate clean logs and labels before attempting complex multi-intersection experiments.

## 2. Network

Initial network:

```text
one four-leg unsignalized intersection
one incoming lane and one outgoing lane per approach
movements: left, through, right
speed limit: 10-13 m/s
control region: 80-120 m upstream of the intersection center
conflict region: manually defined conflict zones around crossing/merging points
```

Rationale:

- A four-leg unsignalized intersection differentiates the prototype from the Part C opinion-dynamics paper, which focuses on roundabouts.
- The geometry is simple enough to debug conflict-zone extraction and label generation.
- Left/through/right movements create enough conflict diversity for coalition formation.

Later extensions:

- two-lane approaches,
- T-intersection,
- roundabout for additional comparison,
- multi-intersection corridor.

## 3. Vehicle Types

Use two vehicle classes:

```text
CAV: controlled by proposed or baseline decision logic
HDV: controlled by SUMO car-following and gap-acceptance behavior
```

HDV behavior profiles:

```text
conservative: larger tau, lower accel, larger minGap
normal: default calibrated parameters
aggressive: smaller tau, higher accel, smaller minGap
```

The first prototype can use SUMO defaults plus three parameter sets. Later, parameters can be calibrated using public trajectory datasets.

## 4. Traffic Demand

Demand dimensions:

```text
traffic volume: low / medium / high
CAV penetration: 0%, 20%, 40%, 60%, 80%, 100%
turning ratio: balanced and left-turn-heavy
HDV behavior mix: conservative / normal / aggressive / mixed
random seeds: at least 5 for prototype, 10+ for paper experiments
```

Suggested first values:

```text
low volume: 300 veh/h/approach
medium volume: 600 veh/h/approach
high volume: 900 veh/h/approach
balanced turn ratio: left 0.25, through 0.50, right 0.25
left-heavy ratio: left 0.40, through 0.45, right 0.15
```

## 5. Conflict Zones

Define conflict zones manually for the first prototype.

Each conflict zone record should contain:

```text
zone_id
center_x
center_y
radius or polygon
incoming movement pairs that may conflict
allowed parallel movement pairs
```

For each vehicle, compute:

```text
route_movement_i
candidate_conflict_zones Z_i
estimated_distance_to_each_zone
predicted_arrival_time tau_i^z
actual_arrival_time tau_i^z after simulation
```

Manual conflict-zone definitions are acceptable for the first version because the goal is algorithm validation, not automatic map parsing.

## 6. Logging Fields

Log at every simulation step:

Vehicle state:

```text
time
veh_id
veh_type: CAV / HDV
route_id
movement: left / through / right
lane_id
x
y
speed
acceleration
heading
distance_to_intersection_center
```

Conflict-zone state:

```text
time
veh_id
zone_id
distance_to_zone
estimated_arrival_time_to_zone
entered_zone: 0/1
exited_zone: 0/1
actual_zone_entry_time
actual_zone_exit_time
```

Interaction state:

```text
time
veh_i
veh_j
zone_id
relative_distance
relative_speed
delta_arrival_time
TTC_or_TTCP
PET_if_available
conflict_edge: 0/1
```

Control output:

```text
time
veh_id
method
coalition_id
assigned_priority
assigned_passing_pattern
waiting_credit
predicted_non_yield_risk
selected_action_or_speed_command
```

## 7. Label Generation

For each HDV-CAV or HDV-vehicle pair `(h, i)` sharing conflict zone `z`, generate a label:

```text
y_{h,i,z} = 1  HDV h takes priority / does not yield
y_{h,i,z} = 0  HDV h yields
```

Use actual crossing order and deceleration behavior:

```text
y_{h,i,z} = 1
if actual_entry_time(h,z) + epsilon_t < actual_entry_time(i,z)
and min_accel(h before z) > -a_yield

y_{h,i,z} = 0
otherwise
```

Recommended initial thresholds:

```text
epsilon_t = 0.5 s
a_yield = 1.5 m/s^2
pre_zone_window = 3.0 s
```

The label script should also store a confidence flag:

```text
label_confidence = high if |entry_time_diff| > 1.0 s
label_confidence = low otherwise
```

Low-confidence labels can be excluded from initial training or used with lower loss weight.

## 8. Prediction Dataset

Each prediction sample:

```text
sample_id
time
target_hdv
interacting_vehicle
zone_id
history_window_states
edge_features
label_yield_non_yield
label_confidence
```

Splits:

```text
train: random seeds 1-6
validation: random seeds 7-8
test: random seeds 9-10
```

Do not split randomly by sample only, because samples from the same scenario are temporally correlated. Use seed/scenario-level splits to reduce leakage.

## 9. Baselines

P0 baselines:

```text
FCFS
rule-based yielding
constant-arrival prediction + greedy allocation
SVM/logistic prediction + greedy allocation
GRU-only prediction + greedy allocation
GRU+graph prediction + fairness-regularized greedy allocation
```

P1 baselines:

```text
generic game-theoretic coordination
opinion-consensus style baseline
efficiency-only coalition allocation
allocation without waiting credit
allocation without prediction uncertainty penalty
```

P2 baselines:

```text
approximate Shapley allocation for small coalitions
learning-only DRL baseline if implementation cost is acceptable
centralized MPC or MILP for small scenarios
```

## 10. Metrics

Prediction metrics:

```text
accuracy
precision
recall
F1
AUC
calibration error if probabilistic calibration is implemented
```

Traffic efficiency:

```text
average delay
average travel time
throughput
stop count
average speed
```

Safety:

```text
minimum TTC or TTCP
PET if extractable
near-conflict count
collision count
hazardous deceleration count
```

Fairness:

```text
maximum waiting time
95th-percentile waiting time
waiting-time standard deviation
Gini coefficient of waiting time
number of vehicles waiting longer than threshold
```

Comfort / environment:

```text
jerk
hard braking count
fuel or energy proxy
```

Runtime:

```text
prediction latency
coalition generation time
allocation time
total decision time per step
```

## 11. Main Prototype Experiments

### P0-E1: Label Sanity Check

Goal: verify that generated yield/non-yield labels are meaningful.

Outputs:

```text
label distribution by traffic volume
label distribution by HDV behavior type
label confidence distribution
examples of high-confidence yield and non-yield cases
```

Stop condition:

```text
If more than 80% of labels fall into one class, adjust scenarios or thresholds.
```

### P0-E2: Prediction Baseline Comparison

Goal: test whether graph interaction improves non-yield risk prediction.

Methods:

```text
constant-arrival rule
SVM/logistic
GRU-only
GRU+graph attention
```

Metrics:

```text
F1
AUC
precision/recall for non-yield class
```

Stop condition:

```text
If GRU+graph does not outperform GRU-only, inspect graph construction and edge features before moving to control experiments.
```

### P0-E3: Control Smoke Test

Goal: verify that the allocator can run without collisions or deadlocks in low and medium demand.

Methods:

```text
FCFS
rule-based yielding
proposed allocation with oracle labels
proposed allocation with predicted labels
```

Metrics:

```text
collision count
deadlock count
average delay
max waiting time
decision runtime
```

Stop condition:

```text
Any repeated collision or deadlock must be debugged before scaling scenarios.
```

### P0-E4: Fairness Mechanism Test

Goal: isolate whether fairness regularization changes waiting-time distribution.

Variants:

```text
full allocation
without fairness term
without waiting credit
```

Metrics:

```text
max waiting time
95th-percentile waiting time
Gini
average delay
minimum TTC/TTCP
```

## 12. Claim-Evidence Matrix

| Claim | Reviewer question | Evidence needed | Dataset/benchmark | Baselines | Metrics | Result placeholder | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Interaction-aware prediction supports HDV risk estimation | Is graph prediction useful beyond hand-crafted features? | Prediction comparison | SUMO logs | constant, SVM/logistic, GRU-only | F1, AUC, recall | TBD | planned |
| Conflict-zone coalition allocation improves control | Does the decision module help beyond simple rules? | Main control comparison | SUMO four-leg intersection | FCFS, rule-based, generic game | delay, throughput, safety | TBD | planned |
| Fairness regularization reduces excessive waiting | Is fairness a real mechanism? | Ablation | SUMO four-leg intersection | full, w/o fairness, w/o credit | max wait, p95 wait, Gini | TBD | planned |
| Prediction robustness matters | Does the method survive noisy prediction? | Noise/stress test | SUMO logs with injected noise | oracle, predicted, noisy predicted | safety, delay, fairness | TBD | planned |

## 13. Execution Priority

| Priority | Experiment | Claim defended | Cost | Dependency | Main/appendix | Stop condition |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | Generate SUMO logs and labels | feasibility | medium | network + logger | main | labels are balanced enough |
| P0 | Prediction baseline comparison | prediction mechanism | medium | labeled data | main | graph model beats or explains failure vs GRU-only |
| P0 | Control smoke test | basic correctness | medium | allocator | main | no repeated collisions/deadlocks |
| P0 | Fairness ablation | fairness mechanism | low | allocator logs | main | fairness metrics move in expected direction or diagnose |
| P1 | Demand and penetration sweep | generalization | high | stable P0 | main | stable across seeds |
| P1 | Prediction-noise robustness | robustness | medium | stable predictor | main/appendix | graceful degradation |
| P2 | Approximate Shapley comparison | allocation analysis | medium | small coalitions | appendix | runtime acceptable |

## 14. Output Files To Produce

Recommended directory structure:

```text
sim/
  networks/
  routes/
  configs/
  scripts/
  logs/
  labels/
  models/
  reports/
```

Core files:

```text
sim/scripts/generate_network.py
sim/scripts/generate_routes.py
sim/scripts/run_sumo.py
sim/scripts/extract_conflict_events.py
sim/scripts/generate_yield_labels.py
sim/scripts/train_predictor.py
sim/scripts/run_allocator.py
sim/scripts/evaluate_metrics.py
```

## 15. No-Fabrication Status

No experimental result has been generated here. All result cells are placeholders and must be filled from actual SUMO runs or verified baseline reports under matching protocols.

