# Work Plan

## Phase 1: Literature Grounding

Goal: determine whether the idea is novel enough for Transportation Research Part C.

Tasks:

- Search recent work on mixed traffic at unsignalized intersections.
- Search cooperative game and coalition game methods for CAV intersection management.
- Search risk-aware and safety-critical CAV coordination.
- Search trajectory/intention/risk prediction for mixed traffic and vehicle interaction modeling.
- Search vehicle-infrastructure cooperation for mixed traffic.
- Build a closest-work table with problem, method, scenario, metrics, and gap.

Pass condition:

- At least 20 high-relevance papers are summarized.
- At least 5 closest papers are compared deeply.
- The final novelty angle is written in one paragraph.

## Phase 2: Learning Module Design

Goal: define a prediction module that supports the game mechanism without becoming an oversized second paper.

Tasks:

- Define prediction inputs: recent trajectories, vehicle type, lane, movement intention if available, neighboring vehicles, conflict-zone context.
- Define prediction outputs: HDV movement intention, arrival-time distribution, yielding probability, and risk score.
- Compare candidate models: LSTM/GRU, temporal Transformer, GNN, temporal graph network.
- Choose a model that is feasible to train and easy to ablate.
- Define simple non-learning predictors as baselines.

Pass condition:

- The prediction module has fixed inputs, outputs, labels, and evaluation metrics.
- The model choice can be justified as supporting the coalition game rather than replacing it.

## Phase 3: Mathematical Formulation

Goal: define a model that can be implemented and explained clearly.

Tasks:

- Define vehicle state, movement intention, and conflict-zone representation.
- Define how predicted HDV uncertainty enters coalition feasibility and coalition value.
- Define coalition feasibility constraints.
- Define coalition value function with delay, throughput, risk, and fairness terms.
- Select payoff or passing-right allocation rule.
- Define rolling-horizon update process.

Pass condition:

- The method can be expressed as equations and pseudocode.
- Every term in the objective can be measured in simulation.

## Phase 4: SUMO Prototype

Goal: build the first working simulation.

Tasks:

- Create a four-leg unsignalized intersection scenario.
- Generate traffic demand with controllable CAV penetration rate.
- Generate or load trajectory histories for the prediction module.
- Implement baseline controllers.
- Implement simple prediction baselines.
- Implement conflict-zone detection and coalition selection.
- Record delay, throughput, stops, TTC/PET, and waiting-time metrics.

Pass condition:

- One complete run can compare the proposed method against FCFS and rule-based yielding.

## Phase 5: Full Experiments

Goal: produce the evidence package for a journal submission.

Tasks:

- Run all demand and penetration-rate scenarios.
- Run ablations for risk, uncertainty, and fairness.
- Run ablations for learning prediction versus rule-based prediction.
- Run robustness tests for HDV behavior.
- Run sensitivity analysis for key weights and horizon length.
- Export tables and figures.

Pass condition:

- All main claims have matching evidence.
- Results include both success cases and failure/limitation analysis.

## Phase 6: Manuscript

Goal: prepare a journal-style manuscript.

Tasks:

- Draft introduction and related work after literature table is stable.
- Write prediction module, problem formulation, and method sections.
- Write experiment setup before interpreting results.
- Write results with conservative claims.
- Write limitations and deployment assumptions.

Pass condition:

- The manuscript has a coherent story: learned mixed-traffic uncertainty -> risk-aware coalition mechanism -> simulation evidence -> limitations.

## Immediate Next Step

Continue with two parallel threads:

1. Deep-read high-risk mixed-traffic game/control papers.
2. Search prediction models for HDV intention, trajectory, yielding, and risk estimation.
