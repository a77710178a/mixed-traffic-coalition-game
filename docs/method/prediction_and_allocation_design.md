# Prediction Label and Allocation Rule Design

Date: 2026-06-16

This document fixes the first implementable version of the prediction target and allocation rule. The goal is to avoid an oversized method while preserving a clear difference from opinion-dynamics consensus and generic game-theoretic coordination.

## 1. Design Decision

The first version should use:

```text
Prediction target: yielding / non-yielding risk probability
Allocation rule: fairness-regularized greedy priority
```

Rationale:

- Yielding risk directly affects conflict-zone safety and passing-right allocation.
- It is easier to label from SUMO trajectories than full multimodal trajectory prediction.
- It aims to go beyond hand-crafted SVM-style intention classification by using temporal and graph interaction features.
- A fairness-regularized greedy allocation is easier to implement than exact Shapley value and can still be compared with approximate Shapley later.

## 2. Prediction Label

For each HDV `h` and CAV or vehicle `i` that may conflict with `h` at conflict zone `z`, define a binary interaction label:

```text
y_{h,i,z} = 1  if HDV h is likely to take priority / not yield
y_{h,i,z} = 0  if HDV h is likely to yield
```

The model predicts:

```text
rho_{h,i,z} = P(y_{h,i,z} = 1 | X_{t-L:t}, G_t, Z)
```

where `rho_{h,i,z}` is the non-yielding risk probability used by the coalition value function.

## 3. Label Generation From Simulation

For SUMO-generated trajectories, labels can be derived from observed conflict-zone arrival order and speed behavior.

For a potential interaction `(h, i, z)`, compute:

```text
tau_h^z : actual arrival time of HDV h at conflict zone z
tau_i^z : actual arrival time of vehicle i at conflict zone z
v_h^-   : HDV speed before the conflict zone
a_h^-   : HDV acceleration before the conflict zone
```

The label can be assigned using a conservative rule:

```text
y_{h,i,z} = 1 if tau_h^z < tau_i^z and h does not decelerate strongly before z
y_{h,i,z} = 0 if tau_h^z > tau_i^z or h decelerates/yields before z
```

Operationally:

```text
y_{h,i,z} = 1 if tau_h^z + epsilon_t < tau_i^z and min(a_h^-) > -a_yield
otherwise y_{h,i,z} = 0
```

where `epsilon_t` is a small time margin and `a_yield` is a yielding deceleration threshold.

This label is intentionally close to the control problem: it measures whether the HDV is expected to take priority in a conflict interaction, not merely whether it turns left, goes straight, or turns right.

## 4. Model Inputs

For each vehicle `i`, use a recent trajectory window:

```text
s_i^{t-L:t} = [p_i, v_i, a_i, lane_i, distance_to_z, heading_i]_{t-L:t}
```

For each interaction edge `(i, j, z)`, use edge features:

```text
e_{ijz} = [
  relative_distance,
  relative_speed,
  predicted_time_to_zone_difference,
  shared_conflict_zone_indicator,
  priority_rule_hint,
  vehicle_type_pair
]
```

The graph is built over vehicles connected by shared conflict zones within the rolling horizon. This differs from using only local proximity because two close vehicles may not conflict, while two separated vehicles may still share a downstream conflict zone.

## 5. First Prediction Architecture

Use a lightweight temporal graph model:

```text
h_i = GRU(s_i^{t-L:t})
beta_{ijz} = softmax_j(MLP([h_i, h_j, e_{ijz}]))
g_i = sum_j beta_{ijz} W h_j
rho_{h,i,z} = sigmoid(MLP([h_h, g_h, e_{hiz}]))
```

Training objective:

```text
L_pred = BCE(y_{h,i,z}, rho_{h,i,z})
       + lambda_cal * calibration_loss
```

If probabilistic calibration is too much for the first version, use only binary cross-entropy and report calibration as future work.

## 6. Prediction Baselines

Use four prediction baselines:

1. **Constant-arrival rule:** predicts priority using current distance and speed.
2. **Hand-crafted SVM/logistic classifier:** uses TTCP and remaining-space features similar in spirit to existing roundabout work.
3. **GRU-only predictor:** temporal history without graph interaction.
4. **GRU + graph attention:** proposed predictor.

The key ablation is:

```text
GRU + graph attention vs. GRU-only
```

This tests whether interaction graph information is useful beyond temporal motion history.

## 7. How Prediction Enters Coalition Value

For a coalition `S`, predicted non-yielding risk enters the risk cost:

```text
C_risk(S) = lambda_r * sum_{(h,i,z) in I(S)} rho_{h,i,z} * R_{h,i,z}
```

where `R_{h,i,z}` is a deterministic safety-margin cost:

```text
R_{h,i,z} = max(0, TTC_safe - TTC_{h,i,z})
          + max(0, PET_safe - PET_{h,i,z})
```

If PET is unavailable in early SUMO logs, use TTCP first:

```text
R_{h,i,z} = max(0, TTCP_safe - |tau_h^z - tau_i^z|)
```

This makes the prediction module decision-relevant: a high non-yielding probability increases the cost of passing patterns that rely on the HDV yielding.

## 8. Fairness-Regularized Greedy Allocation

For each feasible passing pattern `p` of coalition `S`, compute a score:

```text
Score(p, S) = B_eff(p, S)
            - C_risk(p, S)
            - C_unc(p, S)
            - C_fair(p, S)
```

The selected passing pattern is:

```text
p* = argmax_p Score(p, S)
```

The fairness cost is:

```text
C_fair(p, S) = lambda_f * [max_i w_i(p) - mean_i w_i(p)]
             + lambda_g * Gini(w_1(p), ..., w_|S|(p))
```

where `w_i(p)` is predicted waiting time under pattern `p`.

The first implementation can omit the Gini term if needed:

```text
C_fair(p, S) = lambda_f * [max_i w_i(p) - mean_i w_i(p)]
```

This rule is called "greedy" because the best passing pattern is selected within the current rolling horizon rather than solving a global long-horizon assignment.

## 9. Priority Credit

To avoid repeatedly delaying the same vehicle across rolling horizons, maintain a waiting credit:

```text
credit_i(t+1) = gamma * credit_i(t) + waiting_i(t)
```

and add it to the allocation score:

```text
Score(p, S) = B_eff(p, S)
            - C_risk(p, S)
            - C_unc(p, S)
            - C_fair(p, S)
            + lambda_c * sum_i credit_i(t) * served_i(p)
```

where `served_i(p)=1` if vehicle `i` receives a near-term passing opportunity under pattern `p`.

This gives the method a concrete fairness mechanism beyond reporting fairness metrics after the fact.

## 10. Relation To Shapley or Bargaining

Exact Shapley value is not necessary for the first implementation. Instead:

- use fairness-regularized greedy allocation as the main deployable rule;
- optionally compute approximate Shapley values offline for small coalitions;
- compare whether the greedy rule approximates fair allocation with lower runtime.

This avoids making the paper depend on expensive combinatorial allocation while keeping the cooperative-game motivation.

## 11. Difference From High-Risk Prior Work

Compared with opinion-dynamics consensus:

- prior work treats passing plans as opinions and reaches consensus among CAVs;
- this design predicts HDV non-yielding risk with temporal graph features and inserts that risk into coalition value;
- this design explicitly measures waiting fairness.

Compared with generic game-theoretic/subgroup coordination:

- prior work already has cooperative game, Stackelberg game, subgrouping, and PET evaluation;
- this design focuses on conflict-zone graph coalitions and fairness-regularized allocation rather than only maximizing total group reward;
- this design makes prediction robustness and fairness part of the evidence package.

## 12. Immediate Implementation Scope

First prototype:

1. Build SUMO four-leg unsignalized intersection.
2. Log vehicle states and conflict-zone crossing times.
3. Generate `yield / non-yield` labels from observed crossing order and deceleration behavior.
4. Train constant-arrival, SVM/logistic, GRU-only, and GRU+graph predictors.
5. Implement fairness-regularized greedy allocation using predicted risk.
6. Compare against FCFS, rule-based yielding, generic game baseline, and ablations.

## 13. Open Parameters

Initial values to tune:

```text
L              : trajectory history length
Delta_tau      : temporal conflict threshold
epsilon_t      : priority label time margin
a_yield        : yielding deceleration threshold
TTC_safe       : TTC safety threshold
PET_safe       : PET safety threshold
TTCP_safe      : fallback TTCP threshold
lambda_r       : risk weight
lambda_f       : max-wait fairness weight
lambda_g       : Gini fairness weight
lambda_c       : waiting-credit weight
gamma          : waiting-credit decay
S_max          : maximum coalition size
```
