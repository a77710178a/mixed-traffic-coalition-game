# Formal Screening Summary

Date: 2026-06-17

Scope: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized coalition allocation.

This summary consolidates completed screening experiments, mechanism pilots, and the first 10-seed confirmatory run. It does not make final paper claims.

## Completed Runs

| Stage | Runs | Purpose | Report |
| --- | ---: | --- | --- |
| E1 | 45 | Label/event sanity | `docs/experiments/formal_e1_label_sanity_report_20260617.md` |
| E2 | 135 | Main closed-loop screening | `docs/experiments/formal_e2_closed_loop_screening_report_20260617.md` |
| A1 | 40 | Fairness weight ablation | `docs/experiments/formal_a1_fairness_ablation_report_20260617.md` |
| A2 | 30 | Coalition size ablation | `docs/experiments/formal_a2_coalition_size_ablation_report_20260617.md` |
| A3 | 30 | Safe arrival gap ablation | `docs/experiments/formal_a3_safe_gap_ablation_report_20260617.md` |
| J1 | 80 | Joint tuning sweep | `docs/experiments/formal_j1_joint_tuning_report_20260617.md` |
| R1 | 90 | Selected-candidate re-screening | `docs/experiments/formal_rescreen_selected_candidate_report_20260618.md` |
| S1-S4 | 180 | Safety-constrained candidate screen | `docs/experiments/formal_safety_constrained_candidate_screen_report_20260618.md` |
| P1 | 24 | S3 300 s pilot | `docs/experiments/formal_pilot_s3_300s_report_20260618.md` |
| P2 | 48 | CAV waiting tie-breaker 300 s pilot | `docs/experiments/formal_pilot_wait_tiebreaker_300s_report_20260618.md` |
| P3 | 24 | Adaptive release gate 300 s pilot | `docs/experiments/formal_pilot_adaptive_gate_300s_report_20260618.md` |
| P4 | 48 | Adaptive conflict-gap sensitivity | `docs/experiments/formal_pilot_adaptive_gap_sensitivity_300s_report_20260618.md` |
| C1 | 80 | Adaptive gate 300 s confirmatory run | `docs/experiments/formal_confirm_adaptive_gate_300s_report_20260618.md` |
| R2 | 270 | Full-grid adaptive robustness run | `docs/experiments/formal_r2_full_grid_robustness_report_20260619.md` |
| R3 | 30 | High-CAV coarse release-cap sensitivity | `docs/experiments/formal_r3_r4_high_cav_release_cap_report_20260619.md` |
| R4 | 30 | High-CAV gated adaptive-cap sensitivity | `docs/experiments/formal_r3_r4_high_cav_release_cap_report_20260619.md` |
| R5 | 30 | High-CAV adaptive-gate trigger sensitivity | `docs/experiments/formal_r5_adaptive_gate_trigger_report_20260619.md` |
| R6 | 30 | High-CAV lower adaptive-cap boundary test | `docs/experiments/formal_r6_lower_adaptive_cap_report_20260619.md` |
| R7 | 30 | High-CAV projected-PET adaptive guard | `docs/experiments/formal_r7_projected_pet_guard_report_20260619.md` |
| Total | 1274 | Screening, mechanism diagnosis, confirmatory, and robustness runs | this summary |

Runs through J1 were executed locally in the Codex workspace. R1, S1-S4, P1, P2, P3, P4, C1, R2, R3, R4, R5, R6, and R7 were executed on the remote server under the remote-only policy for heavy simulations.

## What We Know

### Data Validity

E1 confirms that the route-zone geometry produces usable event and label data:

- 45 runs
- 3374 route-zone events
- 1193 yield labels
- 1191 high-confidence labels

This is enough to proceed with closed-loop screening and later prediction-model experiments. High-CAV-penetration settings naturally produce fewer HDV-priority labels, so learned HDV-priority claims should be scoped carefully.

### Main Method Signal

E2 shows that the current coalition mechanism has an efficiency signal but not yet a clean safety/fairness result:

| Method | Runs | Throughput ↑ | Mean travel time ↓ | Near conflicts ↓ | Mean PET ↑ | Waiting Gini ↓ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `fcfs` | 45 | 12.20 | 57.40 | 0.33 | 41.92 | 0.5994 |
| `prediction_fcfs` | 45 | 12.20 | 57.40 | 0.33 | 41.92 | 0.5994 |
| `prediction_coalition` | 45 | 13.07 | 54.81 | 0.47 | 38.81 | 0.6066 |

Relative to `fcfs`, `prediction_coalition` improved throughput by 7.10% and reduced mean travel time by 4.52%, but increased near-conflict count and reduced PET.

### Mechanism Diagnosis

A2 shows that coalition size is a major efficiency-safety knob:

- `max_release_count=3`: strongest efficiency, weak PET.
- `max_release_count=2`: more balanced; similar near-conflict count to matched FCFS and better PET than release count 3.
- `max_release_count=1`: too conservative, lower throughput than matched FCFS.

A3 shows that safe gap is not monotonic under the current release logic:

- `safe_arrival_gap_s=0.8` gave the best aggregate efficiency/PET balance in the tested sub-workload.
- `safe_arrival_gap_s=1.6` reduced throughput and did not recover PET.
- This parameter interacts with ordering and HDV close-arrival blocking, so it should be tuned jointly with coalition size.

A1 shows that the fairness weight currently behaves more like a regularizer:

- Higher fairness weights reduce near-conflict counts.
- Waiting Gini improves only slightly.
- Mean/max waiting time does not improve.
- Efficiency decreases as fairness weight increases.

## What We Cannot Claim Yet

Do not claim any of the following yet:

- "The proposed method is universally safer than FCFS in every run."
- "The proposed method is throughput-superior to FCFS."
- "The fairness term substantially improves fairness."
- "Larger safe gap always improves safety."
- "Prediction alone improves closed-loop behavior."
- "The current default parameters are final."

The current evidence supports a narrower claim:

```text
Adaptive route-zone coalition allocation can reduce mean travel time and improve aggregate PET in the 10-seed, 300 s T-junction prototype, but near-conflict count, waiting fairness, conflict-pair count, and low-PET worst cases remain limitations in the full-grid robustness run.
```

## Current Main Candidate

After the P1-P4 mechanism pilots and C1 confirmatory run, the current paper-prototype main candidate is the adaptive release gate:

```text
max_release_count = 2
adaptive_release_enabled = true
adaptive_max_release_count = 3
safe_arrival_gap_s = 1.2
adaptive_min_conflict_arrival_gap_s = 2.4
adaptive_max_occupancy = 0
fairness_weight = 0.0
cav_waiting_tiebreaker_weight = 0.1
```

Candidate roles after C1:

| Candidate | Why |
| --- | --- |
| Adaptive gate `mr=2,amr=3,gap=1.2,cgap=2.4,occ=0,fw=0.0,tb=0.1` | Current main method candidate. It passes the predefined 10-seed aggregate acceptance rule and gives the best confirmed travel-time/PET balance so far. |
| W0 `mr=2,gap=1.2,fw=0.0,tb=0.1` | Conservative ablation and fallback. It improves mean travel time over S3 but does not recover throughput. |
| S3 `mr=2,gap=1.2,fw=0.15` | Safety-leaning ablation. It improves PET/near-conflict behavior in the pilot but fails as an efficiency-improving final default. |
| J1 selected `mr=3,gap=0.8,fw=0.3` | Historical screening candidate. It looked good in the compact joint sweep but failed the later E2-style re-screening safety/fairness check. |

## Completed Joint Sweep

The compact joint tuning sweep was run as queue group `J1`:

```text
max_release_count in {2, 3}
safe_arrival_gap_s in {0.8, 1.2}
fairness_weight in {0.15, 0.3}
volumes = medium, high
penetration = 0.5
seeds = 1..5
duration = 120 s
```

This was 8 settings x 10 runs = 80 runs.

J1 selected:

```text
max_release_count = 3
safe_arrival_gap_s = 0.8
fairness_weight = 0.3
```

Matched against the FCFS subset, the selected candidate produced:

```text
throughput: 10.50 vs 10.10
mean travel time: 64.59 s vs 67.91 s
near-conflict count: 0.20 vs 0.20
min PET: 22.69 s vs 21.24 s
mean PET: 48.78 s vs 47.58 s
waiting Gini: 0.5554 vs 0.5499
```

## Completed Selected-Candidate Re-Screening

The E2-style re-screening with the selected candidate has been completed on the remote server:

```text
seeds = 1..5
volumes = low, medium, high
penetrations = 0.2, 0.5, 0.8
duration = 120 s
methods = fcfs, selected coalition
selected coalition = max_release_count 3, safe_arrival_gap_s 0.8, fairness_weight 0.3
```

The selected candidate reduced mean observed travel time from 57.40 s to 54.80 s and improved average throughput from 12.20 to 12.56 vehicles/run, but it worsened waiting Gini, conflict-pair count, near-conflict count, and PET in the aggregate table.

This result did not justify a final 300 s confirmatory run with the exact selected candidate. The follow-up safety-constrained candidate screen tested four less aggressive or more regularized coalition variants while reusing the completed FCFS reference.

## Completed Safety-Constrained Candidate Screen

The safety-constrained screen promoted S3 as the balanced candidate before the later 300 s pilots:

```text
max_release_count = 2
safe_arrival_gap_s = 1.2
fairness_weight = 0.15
```

Compared with the same 45-run FCFS reference, S3 produced:

```text
throughput: 12.04 vs 12.20
mean travel time: 56.26 s vs 57.40 s
near-conflict count: 0.36 vs 0.33
min PET: 13.48 s vs 13.40 s
mean PET: 42.95 s vs 41.92 s
waiting Gini: 0.6048 vs 0.5994
```

S3 is not a safety-superiority result, but it is a better balanced confirmatory candidate than the original R1 setting because it recovers PET while preserving a modest travel-time benefit.

S2 remains the conservative backup:

```text
max_release_count = 2
safe_arrival_gap_s = 1.2
fairness_weight = 0.3
```

The 300 s pilot has now been completed:

```text
methods = fcfs, S3
seeds = 1,2,3
volumes = medium, high
penetrations = 0.5, 0.8
duration = 300 s
```

P1 result:

```text
throughput: 30.25 vs 31.42
mean travel time: 158.62 s vs 158.33 s
near-conflict count: 0.42 vs 0.50
min PET: 3.41 s vs 3.34 s
mean PET: 92.41 s vs 89.77 s
waiting Gini: 0.6269 vs 0.6279
```

This pilot does not support S3 as an efficiency-improving final default under longer simulation. It supports S3 as a safety-leaning conservative variant: near conflicts, mean PET, min PET, and waiting Gini improve slightly, but throughput and travel time do not.

The follow-up P2 pilot tested this adjustment:

```text
max_release_count = 2
safe_arrival_gap_s = 1.2
cav_waiting_tiebreaker_weight = 0.1
fairness_weight in {0.0, 0.1}
duration = 300 s
runs = 48
```

P2 result:

```text
FCFS throughput: 31.42
S3 throughput: 30.25
W0 throughput: 30.25
W1 throughput: 30.25

FCFS mean travel time: 158.33 s
S3 mean travel time: 158.62 s
W0 mean travel time: 156.75 s
W1 mean travel time: 158.52 s

FCFS mean PET: 89.77 s
S3 mean PET: 92.41 s
W0 mean PET: 92.61 s
W1 mean PET: 92.28 s
```

P2 shows that the CAV waiting tie-breaker improves W0 travel time and preserves the S3 PET/near-conflict behavior, but it does not recover throughput. This suggests the bottleneck is not mainly the fairness ordering; it is the release eligibility structure itself.

P3 tested a geometry-aware adaptive release gate:

```text
base max_release_count = 2
adaptive_max_release_count = 3
safe_arrival_gap_s = 1.2
adaptive_min_conflict_arrival_gap_s = 2.4
adaptive_max_occupancy = 0
fairness_weight = 0.0
cav_waiting_tiebreaker_weight = 0.1
duration = 300 s
runs = 24
```

P3 result:

```text
FCFS throughput: 31.42
W0 throughput: 30.25
adaptive throughput: 30.33

FCFS mean travel time: 158.33 s
W0 mean travel time: 156.75 s
adaptive mean travel time: 156.44 s

FCFS min PET: 3.34 s
W0 min PET: 3.42 s
adaptive min PET: 3.12 s

FCFS mean PET: 89.77 s
W0 mean PET: 92.61 s
adaptive mean PET: 93.31 s
```

P3 supports the adaptive release gate as a useful mechanism direction: it improves travel time and mean PET relative to W0 and gives a small throughput recovery. However, the current `adaptive_min_conflict_arrival_gap_s=2.4` setting reduces min PET, so it is not ready as the final method.

P4 tested stricter conflict-arrival gaps:

```text
adaptive_min_conflict_arrival_gap_s in {3.6, 4.0}
same 300 s protocol
runs = 48
```

P4 result:

```text
W0 throughput: 30.25
adaptive cgap=2.4 throughput: 30.33
adaptive cgap=3.6 throughput: 30.33
adaptive cgap=4.0 throughput: 30.33

W0 mean travel time: 156.75 s
adaptive cgap=2.4 mean travel time: 156.44 s
adaptive cgap=3.6 mean travel time: 156.62 s
adaptive cgap=4.0 mean travel time: 156.62 s

W0 min PET: 3.42 s
adaptive cgap=2.4 min PET: 3.12 s
adaptive cgap=3.6 min PET: 3.12 s
adaptive cgap=4.0 min PET: 3.12 s
```

P4 shows that increasing `adaptive_min_conflict_arrival_gap_s` alone does not repair the min-PET regression. The risky cases are likely passing the static conflict-route gate or being driven by a local entry-gap/PET condition not captured by the current route-conflict rule.

After discussion, the current adaptive `cgap=2.4` candidate was still worth a confirmatory check because its aggregate min PET remained above 3.0 s while mean travel time and mean PET improved. The acceptance rule was fixed before running the larger pilot:

```text
adaptive min_pet_s >= 3.0 s
adaptive near_conflict_count <= FCFS near_conflict_count
adaptive mean_pet_s > FCFS mean_pet_s
adaptive mean_observed_travel_time_s < FCFS mean_observed_travel_time_s
adaptive throughput_arrived >= S3/W0 throughput
```

See `docs/experiments/adaptive_confirmatory_acceptance_rule_20260618.md`.

C1 completed the 10-seed, 300 s confirmatory pilot for adaptive `cgap=2.4`:

```text
FCFS throughput: 31.98
adaptive throughput: 31.45

FCFS mean travel time: 159.35 s
adaptive mean travel time: 157.87 s

FCFS near-conflict count: 0.53
adaptive near-conflict count: 0.48

FCFS min PET: 4.01 s
adaptive min PET: 4.23 s

FCFS mean PET: 90.18 s
adaptive mean PET: 92.63 s
```

C1 passes the predefined aggregate acceptance rule, so adaptive `cgap=2.4` becomes the current main method candidate for the prototype evidence package. The result should still be framed carefully: it supports lower mean travel time, better aggregate PET, and slightly fewer near conflicts, but it does not support throughput superiority, waiting-fairness superiority, or a per-run PET guarantee.

R2 then tested the accepted adaptive gate on the full 300 s robustness grid:

```text
seeds = 1..10
volumes = low, medium, high
CAV penetration = 0.2, 0.5, 0.8
methods = fcfs, prediction_fcfs, adaptive coalition
runs = 270
```

R2 aggregate result:

```text
FCFS throughput: 36.01
adaptive throughput: 37.03

FCFS mean travel time: 141.91 s
adaptive mean travel time: 137.28 s

FCFS near-conflict count: 1.51
adaptive near-conflict count: 1.61

FCFS min PET: 3.13 s
adaptive min PET: 3.46 s

FCFS mean PET: 89.67 s
adaptive mean PET: 91.35 s
```

R2 strengthens the efficiency and aggregate-PET evidence, but it weakens any simple safety-superiority wording because near-conflict count and conflict-pair count increase. CAV penetration sensitivity must be described carefully: 20% CAV penetration gives the largest relative efficiency gain because FCFS has more room for improvement, while 80% CAV penetration gives better absolute PET/near-conflict behavior but smaller efficiency gains because the current release cap cannot fully exploit the larger controllable CAV fleet.

R3/R4 then tested the high-CAV release-cap mechanism:

```text
penetration = 0.8
volumes = low, medium, high
seeds = 1..10
duration = 300 s
R3: wider coarse cap base 3 / adaptive 4
R4: conservative base 2 / adaptive 4 after fixing the gate to fill to adaptive_max_release_count
```

High-CAV aggregate result:

```text
R2 adaptive cap2/3 throughput: 28.60
R3 coarse cap3/4 throughput: 29.97
R4 gated cap2/4 throughput: 28.70

R2 adaptive cap2/3 mean travel time: 153.01 s
R3 coarse cap3/4 mean travel time: 147.07 s
R4 gated cap2/4 mean travel time: 152.74 s

R2 adaptive cap2/3 min PET: 5.52 s
R3 coarse cap3/4 min PET: 4.36 s
R4 gated cap2/4 min PET: 5.51 s

R2 adaptive cap2/3 conflict pairs: 93.07
R3 coarse cap3/4 conflict pairs: 100.80
R4 gated cap2/4 conflict pairs: 93.03
```

The release-set logs explain the mechanism: R3 releases more than two vehicles in about 97.0% of decision steps, while R4 does so in only about 0.44% of decision steps. Therefore, R3 confirms that larger high-CAV release sets can recover efficiency, but the coarse base-cap increase weakens safety margins. R4 confirms that the current geometry-aware gate is safe but too hard to trigger.

R5 then relaxed only the adaptive gate trigger:

```text
base max_release_count = 2
adaptive_max_release_count = 4
adaptive_max_occupancy = 1
adaptive_min_conflict_arrival_gap_s = 3.6
```

High-CAV aggregate result:

```text
R5 throughput: 29.83
R5 mean travel time: 149.08 s
R5 min PET: 5.38 s
R5 mean PET: 95.58 s
R5 conflict pairs: 97.87
R5 near conflicts: 0.30
R5 release count > 2 share: 3.09%
```

R5 is a useful middle point: it recovers most of R3's efficiency while keeping much better min PET than R3, but it still increases conflict-pair and near-conflict counts relative to R2 adaptive. The next high-CAV refinement should be R6: keep `adaptive_max_occupancy=1` and `cgap=3.6`, but lower `adaptive_max_release_count` from 4 to 3 to reduce conflict load.

R6 tested that lower adaptive cap:

```text
base max_release_count = 2
adaptive_max_release_count = 3
adaptive_max_occupancy = 1
adaptive_min_conflict_arrival_gap_s = 3.6
```

R6 result:

```text
R6 throughput: 30.00
R6 mean travel time: 148.73 s
R6 min PET: 5.31 s
R6 mean PET: 95.25 s
R6 conflict pairs: 99.30
R6 near conflicts: 0.37
R6 release count > 2 share: 2.82%
```

R6 is not cleaner than R5: it slightly improves efficiency but increases conflict-pair and near-conflict counts. This suggests scalar cap tuning has reached its useful boundary. The next method step should be a code-level projected-PET guard for adaptive extra releases, not another cap-only threshold sweep.

R7 tested that projected-PET guard:

```text
base max_release_count = 2
adaptive_max_release_count = 4
adaptive_max_occupancy = 1
adaptive_min_conflict_arrival_gap_s = 3.6
projected_min_pet_s = 4.0
```

R7 result:

```text
R7 throughput: 29.30
R7 mean travel time: 151.27 s
R7 min PET: 5.25 s
R7 mean PET: 94.78 s
R7 conflict pairs: 95.10
R7 near conflicts: 0.30
R7 release count > 2 share: 2.58%
```

R7 confirms that an explicit projected-PET guard can reduce the conflict load introduced by R5/R6's more permissive high-CAV gate, but it gives back part of the efficiency recovery. It is therefore a useful safety-shaped mechanism diagnostic, not yet a dominating final high-CAV candidate. The next step should inspect decision-level cases where R5 and R7 differ, rather than running another cap-only sweep.

## Remote Server Use

Current screening runs were local and caused noticeable laptop slowdown. From this point onward, all closed-loop batch experiments should run on the remote server. See `docs/experiments/remote_execution_policy_20260617.md`.

Use the remote server for:

- 300 s confirmatory runs,
- 10-seed or larger sweeps,
- deep learning predictor training,
- repeated robustness runs.

The remote server is not needed for the completed screening stage.
