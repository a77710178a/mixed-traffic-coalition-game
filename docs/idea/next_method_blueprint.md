# Next Method Blueprint

Date: 2026-06-16

## Current Decision

After reading the two high-risk papers, the paper should not be framed as a generic cooperative-game method for mixed unsignalized intersections. The safer and more defensible route is:

> Interaction-aware deep prediction + conflict-zone coalition valuation + fairness-aware passing-right allocation.

## Three Objects To Define Next

### 1. Prediction Object

Define:

- input history length,
- graph nodes and edges,
- HDV labels,
- prediction outputs,
- loss function.

Recommended first version:

```text
Input: past T seconds of vehicle states + conflict-zone graph
Model: GRU encoder + graph attention interaction layer
Output: intention probability, arrival-time interval, yielding/risk probability
```

### 2. Coalition Object

Define:

- which vehicles are eligible for the same local coalition,
- how conflict-zone graph generates candidate coalitions,
- whether non-conflicting vehicles may pass in parallel,
- maximum coalition size.

Recommended first version:

```text
Candidate coalition = vehicles whose predicted trajectories intersect at one or more shared conflict zones within a rolling horizon.
```

### 3. Allocation Object

Define:

- coalition value,
- individual cost,
- fairness penalty,
- passing-right allocation rule.

Recommended first value function:

```text
V(S) = delay_reduction(S)
     + throughput_gain(S)
     - lambda_r * predicted_collision_or_conflict_risk(S)
     - lambda_f * waiting_inequality(S)
     - lambda_u * prediction_uncertainty(S)
```

Recommended first allocation rule:

```text
Use a lightweight Nash-bargaining or approximate Shapley allocation for passing priority.
If too costly, use a fairness-regularized greedy allocation and present Shapley as an analysis baseline.
```

## Immediate Tasks

1. Write the formal problem notation.
2. Choose prediction labels from SUMO-generated trajectories or INTERACTION-like trajectory data.
3. Decide whether the first scene is a four-leg unsignalized intersection or a roundabout.
4. Implement a toy prototype only after the three objects above are fixed.

## Recommended Scene Choice

Use a **four-leg unsignalized intersection** first.

Reason:

- Liu et al. 2026 Part C is roundabout-focused.
- Cui et al. 2026 uses cross-intersection experiments, but its subgrouping is not clearly conflict-zone graph allocation.
- A four-leg setting keeps the problem familiar while allowing conflict-zone graph and fairness claims to be measured clearly.

