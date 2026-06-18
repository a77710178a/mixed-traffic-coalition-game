# Adaptive Confirmatory Acceptance Rule

Date: 2026-06-18

Purpose: define the acceptance criteria before running the 10-seed adaptive gate confirmatory pilot.

This document prevents post-hoc threshold selection. The confirmatory result must be judged against these criteria even if the outcome is mixed.

## Candidate

The confirmatory candidate is the current best adaptive gate:

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

## Confirmatory Workload

```text
seeds = 1..10
volumes = medium, high
penetrations = 0.5, 0.8
methods = fcfs, prediction_coalition
duration = 300 s
runs = 80
```

The workload is intentionally the same as P1-P4 except for the larger seed set.

## Acceptance Criteria

The adaptive candidate is acceptable as the main paper candidate only if all aggregate criteria pass:

| Criterion | Direction | Threshold |
| --- | --- | --- |
| Minimum PET | higher is safer | `adaptive min_pet_s >= 3.0 s` |
| Near conflicts | lower is safer | `adaptive near_conflict_count <= FCFS near_conflict_count` |
| Mean PET | higher is safer | `adaptive mean_pet_s > FCFS mean_pet_s` |
| Mean travel time | lower is more efficient | `adaptive mean_observed_travel_time_s < FCFS mean_observed_travel_time_s` |
| Throughput | higher is more efficient | `adaptive throughput_arrived >= S3/W0 throughput` |

The minimum-PET threshold is not a claim that 3.0 s is universally safe. It is a local acceptance threshold for this prototype stage: small min-PET reductions are acceptable only when they remain above 3.0 s and are accompanied by better mean PET and better efficiency.

## Interpretation Rules

If all criteria pass:

```text
Adaptive gate becomes the current main candidate for the paper prototype.
Next step: full result table, robustness/failure analysis, and method write-up.
```

If min PET fails but efficiency and mean PET pass:

```text
Adaptive gate remains promising but needs an explicit extra-release safety guard.
Next step: implement projected entry-gap/PET guard and repeat a smaller pilot.
```

If efficiency fails:

```text
Adaptive gate should not be promoted.
Next step: return to W0/S3 as conservative candidates or rethink release-set expansion.
```

No final paper claim may be made until the confirmatory output is complete and checked against this rule.
