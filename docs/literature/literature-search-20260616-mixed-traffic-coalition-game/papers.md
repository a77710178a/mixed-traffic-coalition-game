# Literature Search: Mixed-Traffic Coalition Game at Unsignalized Intersections

Date: 2026-06-16

Search purpose: closest-work and opportunity grounding for a Transportation Research Part C-oriented paper.

Target venue/family: Transportation Research Part C / intelligent transportation systems.

Source-quality policy: applied. MDPI papers found during screening were excluded from the scored table.

## Summary

- Closest-work clusters: CAV intersection management surveys; signal-free CAV control; mixed-traffic unsignalized intersection control; cooperative/game-based right-of-way allocation; risk-aware planning.
- Opportunity map: crowded but still open if the paper focuses on conflict-zone local coalitions, HDV uncertainty, risk-constrained coalition value, and fairness-aware passing rights.
- Strongest baselines: FCFS/rule-based yielding, distributed conflict resolution, signal-free optimization, DRL-based mixed-traffic control, safety-critical MCTS, opinion-dynamics negotiation.
- Benchmark/dataset candidates: SUMO synthetic networks first; naturalistic driving datasets for HDV intention/driver-style calibration if available.
- Novelty risks: recent Part C and TITS papers already cover group-benefit control, opinion consensus, and safety-critical mixed-traffic coordination. Direct "cooperative decision-making for mixed traffic at unsignalized intersections" is too broad.
- Recommended next action: differentiate around "risk-constrained coalition game over conflict-zone graph with fairness-aware allocation under uncertain HDV behavior."

## Paper Table

| # | Title | Year | Venue/source | Link | Type | Insight | Completeness | Numeric evidence | Overall | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | A survey on urban traffic control under mixed traffic environment with connected automated vehicles | 2023 | Transportation Research Part C | https://trid.trb.org/View/2210380 | survey | 4 | 4 | N/A | A | Anchor survey for mixed traffic control with CVs/CAVs. |
| 2 | Autonomous and Semi-Autonomous Intersection Management: A Survey | 2020 | IEEE ITS Magazine / arXiv | https://arxiv.org/abs/2006.13133 | survey | 4 | 4 | N/A | A | Frames AIM by conflict detection, priority, centralization, and complexity. |
| 3 | Intersection control with connected and automated vehicles: a review | 2022 | Journal of Intelligent and Connected Vehicles | https://www.emerald.com/jicv/article/5/3/260/225815 | survey | 3 | 4 | N/A | B | Useful for trajectory planning and joint intersection-CAV control structure. |
| 4 | Development of a signal-head-free intersection control logic in a fully connected and autonomous vehicle environment | 2018 | Transportation Research Part C | https://trid.trb.org/View/1515880 | pure method | 4 | 4 | 4 | A | Strong fully-CAV signal-free optimization baseline; not mixed HDV-heavy. |
| 5 | A consensus-based distributed trajectory control in a signal-free intersection | 2019 | Transportation Research Part C | https://www.researchgate.net/publication/330639260_A_consensus-based_distributed_trajectory_control_in_a_signal-free_intersection | pure method | 4 | 4 | 4 | A | Distributed control baseline for signal-free intersection management. |
| 6 | Distributed Conflict Resolution for Connected Autonomous Vehicles | 2018 | IEEE Transactions on Intelligent Vehicles | https://publications.ri.cmu.edu/distributed-conflict-resolution-for-connected-autonomous-vehicles | pure method | 4 | 4 | 4 | A | Foundational conflict-resolution baseline for CAVs. |
| 7 | Cooperative autonomous traffic organization method for connected automated vehicles in multi-intersection road networks | 2020 | Transportation Research Part C | https://research.buaa.edu.cn/en/publications/cooperative-autonomous-traffic-organization-method-for-connected-/ | pure method | 4 | 4 | 4 | A | Includes conflict-resolution at unsignalized intersections plus trajectory and route components. |
| 8 | Connected autonomous vehicles for improving mixed traffic efficiency in unsignalized intersections with deep reinforcement learning | 2021 | Communications in Transportation Research | https://research.chalmers.se/en/publication/530961 | pure method | 4 | 4 | 4 | A | Close mixed-traffic unsignalized-intersection DRL baseline. |
| 9 | Managing Connected Automated Vehicles in Mixed Traffic Considering Communication Reliability: A Platooning Strategy | 2020 | Transportation Research Procedia | https://repo.uni-hannover.de/items/c4be4149-10e2-4cff-a4b9-2efb78698861 | pure method | 3 | 3 | 3 | B | Background for communication reliability and platooning in mixed traffic. |
| 10 | Group-benefit control strategy for connected automated vehicles in mixed traffic at intersections | 2025 | Transportation Research Part C | https://trid.trb.org/View/2537024 | pure method | 4 | 4 | 4 | Risk | Very close recent Part C signal: group benefit + mixed traffic + intersections. |
| 11 | Safety-Critical Multi-Agent MCTS for Mixed Traffic Coordination at Unsignalized Intersections | 2025 | IEEE Transactions on Intelligent Transportation Systems | https://arxiv.org/html/2509.01856v1 | pure method | 4 | 4 | 4 | Risk | Very close on safety-critical mixed traffic coordination; use as safety baseline/threat. |
| 12 | Interactive control strategy of mixed traffic with connected and automated vehicles at unsignalized intersections: a double-layer framework | 2026 | Transportmetrica B | https://www.tandfonline.com/doi/full/10.1080/21680566.2026.2652355 | pure method | 4 | 4 | 4 | Risk | Recent exact-setting paper; must inspect deeply before finalizing claim. |
| 13 | A cooperative decision-making method for CAVs from the perspective of opinion dynamics | 2026 | Transportation Research Part C | https://pure.bit.edu.cn/zh/publications/a-cooperative-decision-making-method-for-cavs-from-the-perspectiv/ | pure method | 5 | 5 | 5 | Risk | Very close Part C paper using right-of-way consensus and HDV intention prediction. |
| 14 | A Game-Theoretic Framework of Interaction and Cooperative Driving for CAVs at Mixed Un-signalized Intersections | 2026 | IEEE Internet of Things Journal | https://dblp.org/pid/224/2513.html | pure method | 4 | 4 | 4 | Risk | Direct game-theoretic mixed unsignalized intersection overlap. |
| 15 | Cooperative multi-vehicle trajectory planning at unsignalized intersections under mixed traffic environment | 2026 | Proceedings of the Institution of Mechanical Engineers, Part D | https://journals.sagepub.com/doi/10.1177/09544070261435053 | pure method | 3 | 4 | 4 | B | Recent mixed-traffic trajectory-planning baseline, especially for priority handling. |

## Clusters

### Cluster 1: Reviews and Field Structure

- Representative papers: Li et al. 2023; Zhong et al. 2020; Wu and Qu 2022.
- What this cluster already solves: defines urban mixed-traffic control and AIM design dimensions, including conflict detection, priority rules, control architecture, and benchmark gaps.
- Remaining gap: reviews do not solve conflict-zone coalition formation under HDV uncertainty.
- Possible rescue or differentiation route: use these papers to justify the benchmark and problem taxonomy, not as direct baselines.
- How it affects the user's paper: introduction and related-work structure should cite them early.

### Cluster 2: Fully CAV Signal-Free Control

- Representative papers: Mirheli et al. 2018; Mirheli et al. 2019; Liu et al. 2018; Wang et al. 2020.
- What this cluster already solves: efficient signal-free CAV control, distributed trajectory coordination, and conflict resolution in connected environments.
- Remaining gap: many assumptions are closer to full CAV or high-connectivity settings; HDV uncertainty and fairness of right-of-way allocation are weaker.
- Possible rescue or differentiation route: position our method as a mixed-traffic transition-stage controller, not a pure AIM controller.
- How it affects the user's paper: these are must-have baselines or at least close references.

### Cluster 3: Mixed-Traffic Unsignalized Intersection Control

- Representative papers: Peng et al. 2021; Luo et al. 2026; Lin et al. 2025; Ji et al. 2026.
- What this cluster already solves: CAV-assisted mixed-traffic improvement, double-layer interaction, safety-critical decision-making, and trajectory planning.
- Remaining gap: a cooperative-game formulation with explicit coalition stability, fairness-aware allocation, and conflict-zone local coalition generation remains a possible angle.
- Possible rescue or differentiation route: avoid competing only on DRL/MCTS performance; emphasize mechanism interpretability and fairness/risk constraints.
- How it affects the user's paper: this cluster is the main novelty threat.

### Cluster 4: Cooperative/Game-Based Right-of-Way Negotiation

- Representative papers: Liu et al. 2026 opinion dynamics; Cui et al. 2026 game-theoretic framework; Hang/Lv line of coalition-game CAV decision-making.
- What this cluster already solves: right-of-way negotiation, consensus, interaction with HDV behavior, and game-theoretic decision-making.
- Remaining gap: direct coalition-value design over conflict-zone graph plus Shapley/nucleolus-style fairness allocation may still be distinguishable, but only after deeper inspection.
- Possible rescue or differentiation route: make the contribution about coalition formation and allocation under safety/fairness constraints, rather than generic game-theoretic interaction.
- How it affects the user's paper: this is the highest-risk cluster.

## Opportunity Map

| Cluster | Status | Open gap | Possible direction | Evidence needed | Risk |
| --- | --- | --- | --- | --- | --- |
| Fully CAV AIM | crowded but open | Pure CAV assumptions are less realistic for transition-stage traffic. | Mixed CAV-HDV coalition controller with uncertain HDV behavior. | CAV penetration-rate sweep and HDV behavior stress tests. | Medium |
| Mixed-traffic learning/control | crowded but open | DRL/MCTS methods can be less interpretable and may not address fairness. | Cooperative-game mechanism with explicit value and allocation terms. | Ablation against DRL/MCTS-inspired or available baselines. | High |
| Game-theoretic right-of-way | covered central claim risk | Recent work already handles game-based mixed unsignalized interactions. | Narrow to conflict-zone coalition formation plus fairness/risk allocation. | Deep read of Liu 2026 and Cui 2026. | High |
| Vehicle-infrastructure cooperation | deployment-system gap | Infrastructure support is often assumed, but sensing/communication quality is under-tested. | Add V2I information reliability/noise sensitivity. | Scenarios with perception/communication noise. | Medium |
| Fairness and social compliance | mechanism gap | Efficiency gains are common; fairness and social-rule compliance are less central. | Use fairness-aware payoff/right-of-way allocation and waiting inequality metrics. | Max waiting time, Gini, tail-delay results. | Medium |

## Benchmark And Dataset Candidates

| Name | Link | Task | Metrics | Baselines | Fit | Risks |
| --- | --- | --- | --- | --- | --- | --- |
| SUMO synthetic unsignalized intersection | https://www.eclipse.org/sumo/ | Controlled simulation for CAV/HDV mixed traffic | delay, throughput, stops, TTC, PET, waiting fairness | FCFS, yielding rules, proposed ablations | High | Synthetic behavior may be criticized without calibration. |
| Naturalistic driving datasets | TBD after data search | HDV intention or driver-style calibration | prediction accuracy, behavior-class realism | SVM/logit/HMM/learning baselines | Medium | Data access and intersection scenario match may be limited. |
| HighD/inD-style trajectory data | TBD after data search | vehicle interaction and trajectory calibration | TTC/PET, gap acceptance, acceleration profile | data-driven HDV model | Medium | Dataset geometry may not match target intersection. |

## Citation And Positioning Cautions

- Claims that need direct citation: mixed traffic is a transition-stage reality; AIM needs realistic evaluation; CAV intersection control has benchmark gaps; HDV uncertainty affects mixed-traffic interaction.
- Papers that may weaken novelty: Liu et al. 2026 Part C opinion dynamics; Fan et al. 2025 Part C group-benefit control; Lin et al. 2025 TITS safety-critical MCTS; Cui et al. 2026 IEEE IoT Journal game-theoretic mixed unsignalized intersections.
- Papers that only support background: surveys and fully-CAV signal-free control papers.

