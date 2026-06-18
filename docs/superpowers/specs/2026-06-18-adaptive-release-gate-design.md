# Adaptive Release Gate Design

Date: 2026-06-18

## Goal

Add a geometry-aware adaptive release gate to the T-junction coalition allocator so the method can recover throughput without abandoning the safer S3 base rule.

## Motivation

The S3 and waiting tie-breaker pilots show a consistent pattern:

- S3 improves PET and near-conflict behavior slightly, but loses throughput against FCFS.
- The CAV waiting tie-breaker improves mean travel time in W0, but does not recover throughput.
- Therefore, the bottleneck is not mainly ordering inside the candidate list. It is the release-set eligibility rule.

The next mechanism should decide when a third CAV can be safely released, not merely reorder already eligible vehicles.

## Scope

This design only changes `prediction_coalition`.

Unchanged behavior:

- `fcfs` still releases one estimated-arrival leader.
- `prediction_fcfs` keeps its current ordering behavior.
- The base S3 rule still uses `max_release_count=2`, `safe_arrival_gap_s=1.2`, and HDV close-arrival protection.
- Heavy experiments remain remote-only.

## Vehicle State Extension

`VehicleState` will carry optional route metadata:

```text
route_id
origin
destination
movement
```

These fields come from SUMO route metadata in closed-loop simulation. Unit tests may construct them directly.

## Adaptive Gate Rule

The allocator first builds the base release set exactly as S3 does.

Then, if adaptive release is enabled, the allocator may add one extra vehicle beyond the base cap.

An extra vehicle is eligible only when all conditions hold:

```text
vehicle is CAV
vehicle priority_probability < risk_threshold
release size is below adaptive_max_release_count
vehicle does not violate HDV close-arrival protection
current conflict-zone occupancy <= adaptive_max_occupancy
for every already released vehicle:
  if route relation is non-conflicting, allow the pair
  if route relation is conflicting, require projected arrival gap >= adaptive_min_conflict_arrival_gap_s
```

Default pilot settings:

```text
adaptive_release_enabled = true
base max_release_count = 2
adaptive_max_release_count = 3
adaptive_min_conflict_arrival_gap_s = 2.4
adaptive_max_occupancy = 0
fairness_weight = 0.0
cav_waiting_tiebreaker_weight = 0.1
safe_arrival_gap_s = 1.2
```

## Route Conflict Relation

The gate uses the existing route-zone geometry artifact:

```text
geometry["conflict_matrix"][route_a][route_b]["conflicts"]
```

If route metadata or conflict geometry is missing, the gate falls back to conservative behavior and does not add the extra vehicle.

This avoids accidental optimism in older configs or unit tests that do not provide geometry.

## Closed-Loop Data Flow

`run_closed_loop_allocation.py` will:

- load the route geometry artifact when `geometry_mode == "route_zones"`;
- enrich candidate `VehicleState` objects with `route_id`, `origin`, `destination`, and `movement`;
- compute current conflict-zone occupancy from candidate vehicles already inside the configured zone radius;
- pass `route_conflict_matrix` and `conflict_zone_occupancy` into `build_decision`;
- write adaptive-gate parameters into run summaries and batch summaries.

## CLI Parameters

Add these optional parameters:

```text
--adaptive-release-enabled
--adaptive-max-release-count
--adaptive-min-conflict-arrival-gap-s
--adaptive-max-occupancy
```

Defaults must preserve existing behavior:

```text
adaptive_release_enabled = false
adaptive_max_release_count = max_release_count
adaptive_min_conflict_arrival_gap_s = 2.4
adaptive_max_occupancy = 0
```

## Tests

Unit tests must verify:

- adaptive gate can add a third low-risk CAV on a non-conflicting route pair;
- adaptive gate refuses the third CAV when route relation conflicts and the arrival gap is too small;
- adaptive gate refuses the extra CAV when conflict-zone occupancy is above the limit;
- adaptive gate still respects high-risk HDV close-arrival protection;
- defaults preserve old behavior when adaptive release is disabled.

Queue and batch tests must verify parameter propagation into commands and summaries.

## Pilot Protocol

After local and remote unit tests pass, run a 300 s remote pilot:

```text
seeds = 1,2,3
volumes = medium,high
penetrations = 0.5,0.8
methods = fcfs,prediction_coalition
duration = 300
max_release_count = 2
adaptive_max_release_count = 3
safe_arrival_gap_s = 1.2
adaptive_min_conflict_arrival_gap_s = 2.4
adaptive_max_occupancy = 0
fairness_weight = 0.0
cav_waiting_tiebreaker_weight = 0.1
```

Compare against FCFS, S3, and W0.

## Decision Criteria

The adaptive gate is promising only if it improves at least one throughput or travel-time metric relative to S3/W0 while keeping these safety indicators no worse than FCFS:

```text
near_conflict_count
min_pet_s
mean_pet_s
```

If it recovers throughput but damages PET, keep it as a diagnostic variant rather than a final method.
