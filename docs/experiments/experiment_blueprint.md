# Experiment Blueprint

## Central Experimental Question

Does interaction-aware prediction-guided fair coalition allocation improve mixed-traffic unsignalized-intersection control compared with rule-based, arrival-order, opinion-consensus, generic game-theoretic, learning-only, non-cooperative, and simplified coalition methods?

## Simulation Platform

Primary simulator: **SUMO**.

The first implementation should use a single unsignalized four-leg intersection. More complex geometries can be added after the method works.

## Scenarios

Start with these scenarios:

- Four-leg unsignalized intersection with left-turn, through, and right-turn movements.
- Balanced demand and unbalanced demand.
- Low, medium, and high traffic volumes.
- CAV penetration rates: 0%, 20%, 40%, 60%, 80%, 100%.
- HDV behavior classes: conservative, normal, aggressive.
- HDV intention/risk prediction settings: rule-based, noisy predictor, learned predictor.
- Optional later scenario: T-intersection or multi-intersection corridor.

## Baselines

Minimum baseline set:

- **FCFS:** first-come-first-served passing order.
- **Rule-based yielding:** priority/yielding rule without coalition optimization.
- **Opinion-consensus style baseline:** passing sequence consensus inspired by opinion dynamics if feasible to reproduce in simplified form.
- **Generic game-theoretic baseline:** cooperative/Stackelberg-style coordination without interaction-aware deep prediction or explicit fairness allocation.
- **Non-cooperative game:** each vehicle minimizes its own delay or cost.
- **Learning prediction + FCFS:** learned HDV prediction supports a simple passing rule.
- **Learning prediction + non-cooperative game:** learned prediction without coalition allocation.
- **Learning-only controller:** DRL or learned policy baseline if feasible and fair to implement.
- **Centralized optimization or MPC:** strong optimization baseline if feasible.
- **Proposed without risk constraint:** ablation for safety mechanism.
- **Proposed without learning prediction:** ablation that uses rule-based HDV uncertainty.
- **Proposed without fairness term:** ablation for allocation fairness.

## Metrics

Efficiency:

- Average delay.
- Throughput.
- Average travel time.
- Stop count.

Safety:

- Minimum TTC.
- PET.
- Conflict count or near-conflict count.
- Collision count, expected to be zero in valid settings.

Prediction:

- Intention prediction accuracy.
- Arrival-time error.
- Yielding/risk classification AUC or F1, if labels are available.
- Calibration error for risk probability, if probabilistic output is used.

Fairness:

- Maximum waiting time.
- Waiting-time standard deviation.
- Gini coefficient of waiting time.

Environmental or comfort indicators:

- Fuel consumption or energy proxy.
- Acceleration/deceleration smoothness.

## Main Experiments

### Experiment 1: Overall Performance

Compare the proposed method with all baselines across demand levels and CAV penetration rates.

Claim tested: the proposed learning-enhanced coalition method improves efficiency while maintaining safety.

### Experiment 2: Prediction Module Evaluation

Compare the chosen learning model with rule-based and simple temporal baselines.

Claim tested: learned HDV intention/risk prediction provides more useful uncertainty estimates for mixed-traffic decision-making.

### Experiment 3: Safety-Risk Constraint Ablation

Compare the full method with an efficiency-only coalition value.

Claim tested: risk-aware coalition value improves TTC/PET and reduces near-conflicts.

### Experiment 4: HDV Uncertainty Robustness

Vary HDV behavior class distribution and intention/arrival-time noise.

Claim tested: learning-based uncertainty modeling improves robustness in mixed traffic, especially at low and medium CAV penetration rates.

### Experiment 5: Fairness Analysis

Compare full method with no fairness term and FCFS.

Claim tested: fairness-aware allocation reduces excessive waiting and waiting-time inequality.

### Experiment 6: Scalability and Rolling-Horizon Sensitivity

Vary traffic volume, horizon length, and maximum coalition size.

Claim tested: conflict-zone local coalition formation is more scalable than global coalition formation.

## Expected Tables and Figures

- Scenario diagram and conflict-zone graph.
- Method pipeline figure.
- Prediction module architecture figure.
- Prediction performance table.
- Average delay and throughput by CAV penetration rate.
- TTC/PET safety comparison.
- Waiting-time distribution or Gini comparison.
- Ablation table.
- Sensitivity analysis for risk weight, fairness weight, and coalition size.

## Risks

- If centralized optimization is too hard to implement fairly, use it only for small-scale scenarios and report scope clearly.
- If Shapley value is computationally expensive, use approximate Shapley or compare with a simpler fair bargaining/allocation rule.
- If safety metrics show little difference, strengthen stress-test scenarios with high demand, aggressive HDVs, and noisy intention prediction.
- If the learning model does not clearly beat simple predictors, use it as a calibrated uncertainty estimator rather than claiming prediction novelty.
- If results only improve at high CAV penetration, reposition the contribution around transition-stage mixed autonomy and explain the required infrastructure support.
- The closest prior work already covers opinion dynamics, generic game-theoretic coordination, subgroup division, and SVM-based HV intention prediction; the experiment section must therefore include fairness and prediction-robustness evidence, not only delay/safety.
