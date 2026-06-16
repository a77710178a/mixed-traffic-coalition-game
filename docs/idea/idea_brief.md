# Idea Brief

## Working Title

**Interaction-Aware Deep Prediction and Fair Coalition Allocation for Mixed Traffic at Unsignalized Intersections**

中文题目：**面向混行无信号交叉口的交互感知深度预测与公平联盟分配方法**

## Core Positioning

This paper should not be framed as "applying cooperative game theory to intersection scheduling." That framing is too broad and likely too close to existing CAV coordination work.

The stronger framing is:

> In mixed traffic, CAVs can cooperate, but HDVs are uncertain and cannot be directly controlled. At unsignalized intersections, there is no signal phase to impose an external passing order. The core problem is how to use interaction-aware HDV prediction to support temporary, stable, safe, and fair coalition-level passing decisions.

## Main Contribution Boundary

The paper should have **one main innovation**:

> A conflict-zone-driven coalition allocation framework that is guided by interaction-aware HDV prediction and explicit fairness/risk penalties.

Other elements should be presented as supporting components, not separate equal contributions:

- A deep learning prediction module estimates HDV intention, arrival uncertainty, and yielding/risk probability.
- Conflict-zone modeling defines which vehicles need to negotiate.
- Vehicle-infrastructure information improves conflict and intention estimation.
- Fairness-aware payoff allocation explains why vehicles accept the coalition result.

This keeps the paper coherent: every module serves the coalition game.

## Problem Statement

Given a stream of CAVs and HDVs approaching an unsignalized intersection, predict HDV intention/risk and determine local passing coalitions and passing priorities that reduce delay and stop-and-go behavior while maintaining safety and fairness under uncertain HDV behavior.

The system receives vehicle states, recent trajectory histories, intended movements when available, estimated arrival times, and infrastructure-assisted conflict information. It outputs HDV intention/risk estimates, coalition groups, and passing decisions over a rolling horizon.

## Root Challenge

The difficulty is not only deciding who passes first. The harder issue is that:

- Vehicles interact through conflict zones, not only through lanes.
- HDVs may not follow cooperative commands, and their intentions or yielding behavior must be inferred.
- Pure efficiency optimization can produce unfair or unsafe waiting patterns.
- A large global coalition is computationally heavy and behaviorally unrealistic.
- A local rule such as FCFS cannot exploit non-conflicting parallel movements.

## Core Insight

Deep learning should handle the hard-to-model part: HDV intention, arrival uncertainty, and yielding/risk probability. Cooperative game theory should handle the decision part: interpretable coalition formation and passing-right allocation. Vehicles that share conflict zones form temporary games; vehicles without conflict should be allowed to pass in parallel. Coalition value should be penalized by learned safety risk and unfair waiting, so that the selected coalition is not merely fast but also acceptable under mixed traffic.

## Method Sketch

1. Use recent vehicle trajectories and surrounding context to predict HDV intention, arrival interval, and yielding/risk probability.
2. Detect conflict zones and build a vehicle-conflict graph.
3. Generate feasible local coalitions from the conflict graph and prediction outputs.
4. Define coalition value using delay reduction, throughput gain, learned safety-risk penalty, and fairness penalty.
5. Allocate passing rights or coalition benefits using a cooperative-game rule or a simpler fair bargaining approximation.
6. Execute decisions in a rolling horizon and update predictions and coalitions as new vehicles arrive.

## Candidate Contribution Claims

These are draft claims and must be supported by experiments before being used strongly in the paper:

1. The proposed conflict-zone coalition mechanism reduces average delay and stop count compared with FCFS and rule-based yielding.
2. Risk-constrained coalition value improves TTC/PET or TTCP-based safety indicators compared with efficiency-only coalition control.
3. Learning-based HDV prediction improves robustness under low and medium CAV penetration rates compared with rule-based uncertainty models.
4. Fairness-aware allocation reduces maximum waiting time and waiting-time inequality without sacrificing much throughput.

## Novelty Status

Novelty is **not yet verified**. The closest-work search should focus on:

- mixed traffic at unsignalized intersections,
- CAV and HDV cooperative control,
- coalition allocation or cooperative game for intersection management,
- group-benefit control at intersections,
- risk-aware CAV coordination,
- trajectory/intention prediction for mixed traffic,
- graph neural networks or temporal models for vehicle interaction,
- vehicle-infrastructure cooperation for mixed traffic.

## Recommended Paper Shape

1. Introduction: mixed traffic makes unsignalized intersection cooperation difficult.
2. Related work: CAV intersection management, mixed traffic control, cooperative games, risk-aware coordination.
3. Prediction module: input representation, model choice, outputs, and uncertainty/risk estimation.
4. Problem formulation: conflict zones, vehicle types, uncertainty, objectives.
5. Coalition allocation method: formation, value function, allocation, rolling-horizon execution.
6. Simulation design: SUMO scenarios, baselines, metrics, penetration rates.
7. Results: prediction quality, efficiency, safety, fairness, robustness, ablations.
8. Discussion: limits, deployment assumptions, future work.

## Explicit Non-Goals

- Do not claim the paper is the first game-theoretic method for mixed unsignalized intersections.
- Do not claim the paper is the first to use HDV intention prediction in this setting.
- Do not make Shapley value or nucleolus mandatory unless the final method really needs them.
- Do not let the learning module become a second main paper.
