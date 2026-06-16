# Formal Problem Formulation

Date: 2026-06-16

Working title: **Interaction-Aware Deep Prediction and Fair Coalition Allocation for Mixed Traffic at Unsignalized Intersections**

This document defines the mathematical objects needed before implementation: traffic state, conflict-zone graph, prediction outputs, feasible coalitions, coalition value, and fairness-aware allocation.

## 1. Setting

We consider an unsignalized intersection with mixed traffic, where connected automated vehicles (CAVs) and human-driven vehicles (HDVs) approach the conflict area from multiple incoming lanes. Let

```text
N(t) = C(t) union H(t)
```

denote the set of vehicles within the control region at decision time `t`, where `C(t)` is the set of CAVs and `H(t)` is the set of HDVs. The control region covers the upstream observation area, the conflict-zone area, and the downstream exit buffer.

Each vehicle `i in N(t)` has state

```text
x_i(t) = [p_i(t), v_i(t), a_i(t), l_i(t), m_i(t), type_i]
```

where `p_i` is position, `v_i` is speed, `a_i` is acceleration, `l_i` is lane index, `m_i` is the intended movement if known or estimated, and `type_i` indicates CAV or HDV. For HDVs, `m_i` and future motion are uncertain.

The objective is to determine local passing coalitions and passing priorities over a rolling horizon so that vehicles can cross shared conflict zones efficiently, safely, and fairly.

## 2. Conflict-Zone Graph

The intersection is represented by a set of conflict zones

```text
Z = {z_1, z_2, ..., z_K}.
```

A conflict zone may correspond to a crossing point, merging point, diverging point, or a small conflict area depending on map resolution. For each vehicle `i`, its candidate route induces a set of conflict zones

```text
Z_i = {z in Z : vehicle i may pass through z within the horizon}.
```

We construct a vehicle conflict graph

```text
G_t = (N(t), E_t),
```

where an edge `(i, j) in E_t` exists if vehicles `i` and `j` are predicted to share at least one conflict zone within the rolling horizon:

```text
(i, j) in E_t iff Z_i cap Z_j != empty and |tau_i^z - tau_j^z| <= Delta_tau
```

for some `z in Z_i cap Z_j`, where `tau_i^z` is the predicted arrival time of vehicle `i` at conflict zone `z`, and `Delta_tau` is a temporal conflict threshold.

This graph is the main structural difference from global intersection scheduling. Vehicles without conflict edges do not need to be placed in the same negotiation problem and may be allowed to pass in parallel.

## 3. Interaction-Aware Prediction

For each HDV `h in H(t)`, the prediction module estimates future intention, arrival uncertainty, and interaction risk from recent trajectories and conflict-zone context. Let `X_{t-L:t}` denote the past `L` time steps of all observed vehicle states. The prediction module is

```text
Phi_theta : (X_{t-L:t}, G_t, Z) -> Y_t.
```

The output for each HDV `h` contains:

```text
pi_h^m      : probability distribution over movement intentions,
mu_h^z      : predicted arrival time at conflict zone z,
sigma_h^z   : arrival-time uncertainty at conflict zone z,
rho_h^{ijz} : risk or non-yielding probability in interaction with vehicle i at zone z.
```

A practical first model is a GRU encoder plus graph attention:

```text
e_i = GRU(x_i(t-L), ..., x_i(t))
alpha_ij = attention(e_i, e_j, phi_ij)
g_i = sum_{j in N_i} alpha_ij W e_j
y_i = MLP([e_i, g_i, c_i])
```

where `phi_ij` contains relative position, relative speed, shared conflict-zone indicators, and predicted time-to-arrival difference. `c_i` encodes static conflict-zone and lane-context features.

The learning module should be evaluated independently, but its main role is to provide uncertainty-aware inputs to the coalition allocation module rather than to replace the decision mechanism.

## 4. Candidate Coalitions

A candidate coalition is a local vehicle group that must coordinate because its members are mutually linked through conflict-zone interactions. For each connected component or dense local subgraph of `G_t`, we generate candidate coalitions

```text
S subseteq N(t), |S| <= S_max.
```

A coalition `S` is feasible if:

1. all vehicles in `S` can be assigned a conflict-free passing order or compatible parallel passing pattern;
2. the predicted safety risk of the passing pattern does not exceed a threshold;
3. each CAV in `S` can execute its assigned motion within acceleration and jerk limits;
4. HDV behavior uncertainty is accounted for through prediction intervals or risk penalties.

Unlike subgrouping based only on proximity to the intersection center, the coalition should be generated from the conflict-zone graph. This distinction is important because vehicles close to the intersection are not necessarily mutually conflicting, while vehicles in different lanes may share a downstream conflict zone.

## 5. Coalition Value

For a feasible coalition `S`, define the coalition value as the net benefit of coordinating `S` compared with a baseline passing policy such as FCFS or rule-based yielding:

```text
V(S) = B_eff(S) - C_risk(S) - C_fair(S) - C_unc(S).
```

The efficiency benefit is

```text
B_eff(S) = lambda_d * Delta_delay(S) + lambda_q * Delta_throughput(S),
```

where `Delta_delay(S)` is delay reduction relative to the baseline and `Delta_throughput(S)` is local throughput gain.

The risk cost is computed from predicted conflict probabilities:

```text
C_risk(S) = lambda_r * sum_{(i,j,z) in I(S)} rho_{ijz} * g(TTC_{ijz}, PET_{ijz}, TTCP_{ijz}),
```

where `I(S)` is the set of pairwise zone-level interactions within `S`, and `g(.)` increases when safety margins are small.

The uncertainty cost penalizes unreliable predictions:

```text
C_unc(S) = lambda_u * sum_{h in H(S)} sum_{z in Z_h} sigma_h^z.
```

The fairness cost penalizes excessive waiting imbalance:

```text
C_fair(S) = lambda_f * F(w_1, w_2, ..., w_|S|),
```

where `w_i` is the predicted waiting time of vehicle `i` under the proposed allocation. A first implementation can use one of:

```text
F_max = max_i w_i - mean_i w_i
F_var = variance(w_i)
F_gini = Gini(w_1, ..., w_|S|)
```

The fairness term is not decorative. It is the main mechanism separating the proposed method from prior work that optimizes group reward or consensus without explicitly measuring waiting inequality.

## 6. Passing-Right Allocation

After selecting a coalition and feasible passing patterns, the method allocates passing rights or priority scores to vehicles in the coalition. The allocation rule should satisfy three practical requirements:

1. vehicles with high safety risk should not be forced into aggressive maneuvers;
2. long-waiting vehicles should receive increasing priority;
3. non-conflicting vehicles should be allowed to pass in parallel when possible.

A lightweight allocation score can be

```text
A_i(S) = eta_1 * marginal_efficiency_i(S)
       - eta_2 * marginal_risk_i(S)
       + eta_3 * waiting_credit_i
       - eta_4 * uncertainty_exposure_i.
```

The passing priority is then obtained by sorting `A_i(S)` subject to safety constraints and parallel-passing compatibility.

If computation permits, we can compare the lightweight score with approximate Shapley allocation:

```text
phi_i(V) = sum_{S subseteq N\{i}} |S|!(n-|S|-1)! / n! * [V(S union {i}) - V(S)].
```

However, Shapley value should not be mandatory in the first implementation. If exact Shapley is too expensive, approximate Shapley can be used as an analysis baseline, while a fairness-regularized greedy rule serves as the deployable method.

## 7. Rolling-Horizon Execution

At each decision step:

1. collect recent trajectories and infrastructure observations;
2. update HDV intention/risk predictions;
3. build the conflict-zone graph;
4. generate feasible local coalitions;
5. evaluate coalition value and fairness-aware allocations;
6. execute the first action or passing priority in a rolling horizon;
7. update the graph and predictions at the next step.

This rolling-horizon design allows the method to adapt when HDVs deviate from predicted behavior.

## 8. Draft Algorithm

```text
Algorithm: Interaction-Aware Fair Coalition Allocation

Input:
  vehicle states X_{t-L:t}
  conflict-zone map Z
  rolling horizon T
  maximum coalition size S_max

Output:
  coalition assignments
  passing priorities
  executable CAV commands

1. Predict HDV intention, arrival time, uncertainty, and risk using Phi_theta.
2. Build vehicle conflict graph G_t from predicted shared conflict zones.
3. Generate candidate coalitions from local components of G_t.
4. For each coalition S:
     a. enumerate feasible passing patterns;
     b. estimate delay, safety margins, uncertainty, and waiting times;
     c. compute V(S).
5. Select coalitions and passing patterns that maximize total value under safety constraints.
6. Allocate passing rights using fairness-aware priority scores or approximate Shapley values.
7. Execute first-step CAV actions and repeat at t + Delta_t.
```

## 9. Claims This Formulation Is Designed To Test

This formulation is designed to test the following claims. They should not be stated as findings until experiments support them:

- Whether interaction-aware prediction improves decision robustness compared with hand-crafted or rule-based HDV intention models.
- Whether conflict-zone graph coalitions reduce unnecessary negotiation between non-conflicting vehicles.
- Whether risk-constrained coalition value improves safety margins compared with efficiency-only coordination.
- Whether fairness-aware allocation reduces tail waiting time and waiting-time inequality compared with group-reward-only methods.

## 10. Open Design Choices

The next implementation decision should resolve:

- whether the first prediction label is intention, yielding, risk, or arrival time;
- whether the first allocation rule uses Nash bargaining, approximate Shapley, or fairness-regularized greedy priority;
- whether the first scenario uses only SUMO-generated labels or also an external trajectory dataset;
- whether safety uses TTC/PET/TTCP consistently across all baselines.
