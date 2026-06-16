# Learning Module Design

## Role in the Paper

The learning module should not replace the coalition game. Its role is to estimate the uncertain parts of mixed traffic that are hard to model manually:

- HDV movement intention.
- Arrival-time uncertainty.
- Yielding or non-yielding probability.
- Local interaction risk.

The coalition game remains the decision-making core.

## Input Candidates

Vehicle-level inputs:

- Position.
- Speed.
- Acceleration.
- Lane ID.
- Distance to conflict zone.
- Vehicle type: CAV or HDV.
- Recent trajectory history.
- Intended movement if available: left, through, right.

Interaction inputs:

- Nearby vehicles within a detection radius.
- Relative distance and relative speed.
- Conflict-zone relation.
- Time-to-arrival difference at conflict points.
- Priority/yielding relation if a rule-based estimate exists.

Infrastructure inputs:

- Conflict-zone map.
- Lane geometry.
- Roadside perception observations if assumed.
- Communication reliability or observation noise if tested.

## Output Candidates

Minimum outputs:

- HDV movement intention probability.
- Arrival time or arrival-time interval at each relevant conflict zone.
- Risk probability or risk score for each candidate passing order.

Optional outputs:

- Yielding probability.
- Driver-style class: conservative, normal, aggressive.
- Trajectory distribution over a short horizon.

## Candidate Models

### Option A: LSTM or GRU

Pros:

- Easy to implement.
- Lower data and compute requirements.
- Good first baseline.

Cons:

- Weak at modeling multi-vehicle interaction unless manually engineered.

Best use:

- Initial prototype and baseline predictor.

### Option B: Temporal Transformer

Pros:

- Strong sequence modeling.
- Can model longer temporal context.

Cons:

- More data hungry.
- May look heavy if the dataset is small.

Best use:

- If trajectory histories are long and enough training data can be generated.

### Option C: Graph Neural Network with Temporal Encoder

Pros:

- Natural fit for vehicle interaction and conflict-zone graphs.
- Aligns well with the later coalition graph.

Cons:

- More implementation complexity.
- Needs careful ablation to avoid looking like decorative deep learning.

Best use:

- Recommended final direction if feasible.

### Option D: Hybrid Lightweight Model

Example: GRU for each vehicle history + graph attention over interacting vehicles.

Pros:

- Strong enough to be modern.
- More feasible than a large Transformer.
- Naturally connects prediction to conflict-zone coalition formation.

Cons:

- Needs clean data pipeline.

Best use:

- Recommended practical starting point.

## Recommended Choice

Start with **Option D: GRU + graph attention**.

Reason:

- It adds a real deep learning component.
- It models temporal HDV behavior and vehicle interaction.
- It can output uncertainty/risk for the coalition game.
- It is easier to implement than a full spatiotemporal Transformer.

## Prediction Baselines

Use at least:

- Constant-velocity prediction.
- IDM/MOBIL or rule-based behavior estimate.
- GRU-only prediction without graph interaction.
- Proposed GRU + graph attention.

## How Prediction Enters the Coalition Game

The prediction module outputs:

- arrival-time distribution,
- movement intention probability,
- yielding/risk probability.

These become inputs to:

- coalition feasibility constraints,
- conflict probability,
- risk penalty in coalition value,
- robust passing-order selection.

Draft coalition value:

```text
V(S) = efficiency_gain(S)
       - lambda_r * predicted_risk(S)
       - lambda_f * unfairness(S)
       - lambda_u * uncertainty_penalty(S)
```

## First Implementation Target

For the first prototype:

1. Simulate mixed traffic in SUMO.
2. Export per-vehicle trajectory histories.
3. Generate labels from known routes, arrival times, and conflict events.
4. Train GRU-only and GRU+graph attention predictors.
5. Feed predictions into the coalition game.

