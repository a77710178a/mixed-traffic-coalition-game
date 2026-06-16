# High-Risk Literature Deep-Read Plan

Date: 2026-06-16

Purpose: identify the closest prior work before freezing the paper's novelty claim.

## Why Start Here

The topic is viable, but several recent papers already cover mixed traffic, unsignalized intersections, cooperative decision-making, game theory, HDV uncertainty, and safety-critical coordination. The first task is not writing formulas; it is identifying the exact boundary where our paper can be different.

## Five Papers To Deep Read First

| Priority | Paper | Why it is risky | What to extract |
| --- | --- | --- | --- |
| 1 | Liu et al., 2026, *A cooperative decision-making method for CAVs from the perspective of opinion dynamics*, Transportation Research Part C | Covers cooperative decision-making, rights-of-way as opinions, HDV intention prediction, and HIL validation. | Scenario, right-of-way formulation, HDV prediction method, baselines, safety/efficiency metrics, social-compliance mechanism. |
| 2 | Cui et al., 2026, *A Game-Theoretic Framework of Interaction and Cooperative Driving for CAVs at Mixed Unsignalized Intersections*, IEEE Internet of Things Journal | Directly covers game-theoretic mixed unsignalized intersections and HDV parameter updating. | Game type, CAV-CAV and CAV-HDV formulation, HDV behavior update, experimental scene, metrics, limitations. |
| 3 | Fan et al., 2025, *Group-benefit control strategy for connected automated vehicles in mixed traffic at intersections*, Transportation Research Part C | Recent Part C paper on group benefit in mixed traffic, though focused on signalized intersections and MADDPG. | Whether group benefit is equivalent to coalition value, how mixed traffic is modeled, whether fairness is considered. |
| 4 | Lin et al., 2025, *Safety-Critical Multi-Agent MCTS for Mixed Traffic Coordination at Unsignalized Intersections/Roundabouts*, IEEE TITS | Covers safety-critical mixed-traffic coordination, HDV uncertainty, PET, and AV penetration-rate experiments. | Safety model, risk metrics, HDV uncertainty model, PET/TTC protocol, penetration-rate settings, MCTS baselines. |
| 5 | Luo et al., 2026, *Interactive control strategy of mixed traffic with connected and automated vehicles at unsignalized intersections: a double-layer framework*, Transportmetrica B | Exact scenario overlap: mixed traffic with CAVs at unsignalized intersections. | Upper/lower layer roles, whether coalition/game allocation exists, HDV modeling, benchmark scenarios, unresolved gaps. |

## Deep-Read Matrix

For each paper, fill:

| Field | Notes |
| --- | --- |
| Scenario | Four-leg intersection, roundabout, signalized intersection, merge, etc. |
| Vehicle mix | CAV/AV/HDV definitions and penetration rates. |
| Decision object | Right-of-way, trajectory, acceleration, lane choice, signal timing, coalition, etc. |
| Method core | Opinion dynamics, game theory, MCTS, MADDPG, MPC, optimization, etc. |
| HDV uncertainty | None, rule-based, SVM, IDM, probabilistic, twin-game parameter update, etc. |
| Safety mechanism | TTC, PET, CBF, hard constraints, risk field, safety pruning, etc. |
| Fairness/social rule | Whether waiting fairness, social compliance, or priority equity is explicit. |
| Cooperation concept | Group benefit, consensus, game interaction, coalition formation, or only coordination. |
| Baselines | Rule-based, game-based, RL, MCTS, optimization, FCFS, etc. |
| Evaluation strength | SUMO, custom simulator, naturalistic data, HIL, human-in-loop, multiple geometries. |
| What is already covered | The exact claim this paper would block. |
| Remaining gap | What our paper can honestly add. |

## Preliminary Differentiation Hypothesis

Do not claim novelty yet. The current working hypothesis is:

> Existing work studies cooperative decision-making, group-benefit control, game-theoretic interaction, and safety-critical planning. Our possible distinct angle is a conflict-zone graph that dynamically forms local coalitions, combined with a risk-constrained coalition value and fairness-aware allocation of passing rights under HDV uncertainty.

This hypothesis survives only if the five high-risk papers do not already combine all three elements:

1. conflict-zone-driven local coalition formation,
2. risk-constrained coalition value,
3. cooperative-game allocation/fairness under uncertain HDV behavior.

## Immediate Work Order

1. Obtain full text for the five high-risk papers.
2. Fill the deep-read matrix.
3. Rewrite the idea brief based on the strongest remaining gap.
4. Only then finalize equations and SUMO experiment design.

## Early Red Lines

Avoid these claims unless the deep read proves they are safe:

- "First cooperative decision-making method for mixed traffic at unsignalized intersections."
- "First game-theoretic framework for mixed unsignalized intersections."
- "First method considering HDV uncertainty."
- "First safety-aware mixed-traffic coordination method."

Safer possible claims:

- "A coalition-formation perspective for conflict-zone-level mixed-traffic coordination."
- "A risk-constrained coalition value function for local passing-right negotiation."
- "A fairness-aware cooperative-game allocation mechanism for mixed-traffic unsignalized intersections."

