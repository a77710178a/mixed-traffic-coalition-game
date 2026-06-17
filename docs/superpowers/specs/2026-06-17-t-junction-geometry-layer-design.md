# T-Junction Geometry Layer Design

Date: 2026-06-17

Status: design approved in discussion; awaiting written-spec review before implementation

## 1. Goal

The geometry layer will replace the current single center-circle conflict-zone simplification with a reproducible T-junction model that can support a journal paper method section. The main purpose is to make the coalition game depend on route-level geometric conflicts rather than only on distance to the intersection center.

The design must satisfy three requirements:

1. It must match the paper setting: mixed CAV/HDV traffic at an unsignalized T-intersection.
2. It must produce conflict-zone graph inputs for prediction, coalition generation, safety metrics, and passing-right allocation.
3. It must remain implementable in the existing SUMO prototype without requiring a full HD-map toolchain.

## 2. Source Basis

The design uses public engineering and simulation references only as geometry constraints and sanity checks, not as claimed experimental evidence.

| Source | Relevant use in this project |
| --- | --- |
| FDOT Design Manual 212, Intersections | Treats 3-leg/T intersections as conventional at-grade intersections, defines control types, functional area, and recommends intersection angles near 90 degrees with heavy skew avoided. |
| FHWA Older Road User Handbook, Chapter 7 | Supports using 11 to 12 ft, about 3.35 to 3.66 m, as a reasonable intersection lane-width range; also motivates turn-path and lane-keeping sensitivity. |
| ODOT Analysis Procedures Manual v2, Chapter 4 Safety | Defines a T-intersection as one roadway ending at another and gives the conventional all-movement T-intersection conflict-point sanity check. |
| SUMO Intersections documentation | Confirms the need for internal links to model movement inside intersections, right-of-way behavior, junction blocking, and turning-speed reduction related to turning radius. |
| Li and Liu, PLOS One 2020, autonomous intersection management | Provides a close example of using a static conflict matrix plus dynamic occupation information, motivating our movement-level conflict graph. |

Reference URLs:

- https://fdotwww.blob.core.windows.net/sitefinity/docs/default-source/roadway/fdm/2023/2023fdm212intersections.pdf
- https://highways.dot.gov/safety/other/older-road-user/handbook-designing-roadways-aging-population/chapter-7-intersections
- https://www.oregon.gov/odot/Planning/Documents/APMv2_Ch4.pdf
- https://sumo.dlr.de/docs/Simulation/Intersections.html
- https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0235644

## 3. Geometry Decision

Use an orthogonal three-leg T-intersection as the formal scenario:

- Major road: north-south, two-way, one inbound and one outbound lane per direction.
- Minor road: east branch, two-way, one inbound and one outbound lane.
- Missing west leg: no west approach, no west destination.
- Control: unsignalized, with main-road priority as the default traffic-rule hint and explicit conflict constraints used by the proposed controller.

This gives a realistic but still controlled geometry. The earlier four-leg network remains useful as a debugging baseline, but it should not be the main paper scene.

## 4. Coordinate System

Use a right-handed 2D coordinate system:

```text
 origin C = (0, 0), the nominal junction center
 x-axis   = east positive
 y-axis   = north positive
```

Approach centerlines:

```text
 N approach: x = 0, y in [0, +L]
 S approach: x = 0, y in [-L, 0]
 E approach: y = 0, x in [0, +L]
```

Right-hand traffic is assumed. With lane width `w_lane`, the nominal lane centers are:

| Lane | Centerline |
| --- | --- |
| N inbound, southbound | `x = -w_lane / 2` |
| N outbound, northbound | `x = +w_lane / 2` |
| S inbound, northbound | `x = +w_lane / 2` |
| S outbound, southbound | `x = -w_lane / 2` |
| E inbound, westbound | `y = +w_lane / 2` |
| E outbound, eastbound | `y = -w_lane / 2` |

This lane-offset convention is important: opposing through movements on the major road are not automatically conflicting just because both pass near the center.

## 5. Nominal Parameters

The first formal scenario uses a passenger-car, low-speed urban T-junction setting.

| Parameter | Symbol | Nominal value | Notes |
| --- | --- | ---: | --- |
| Approach length | `L` | `120 m` | Matches the current prototype; can be extended to `200 m` for long-queue stress tests. |
| Lane width | `w_lane` | `3.5 m` | Within the common 11 to 12 ft engineering range. |
| Speed limit | `v_limit` | `11.11 m/s` | About `40 km/h`. |
| Nominal turning radius | `r_turn` | `10 m` | Low-speed passenger-car scenario value; sensitivity should use `8, 12, 15 m`. |
| Vehicle length | `l_veh` | `4.5 m` | Passenger-car default. |
| Vehicle width | `w_veh` | `1.8 m` | Passenger-car default. |
| Lateral safety buffer | `b_safe` | `0.5 m` | Sensitivity can use `0.75 m` for conservative runs. |
| Control-region distance | `d_control` | `45 m` | Vehicles inside this path distance are eligible for graph construction. |
| Path sampling interval | `ds` | `0.25 m` | Used to build swept-area polygons. |
| Static overlap tolerance | `A_min` | `0.25 m^2` | Removes numerical sliver overlaps. |

Only `r_turn`, demand level, CAV penetration, HDV behavior mix, and safety-buffer size should be varied in the first evidence package. Lane width and approach length are geometry controls, not main claims.

## 6. Legal Movement Set

The active approaches are:

```text
 A = {N, E, S}
```

The legal route set is:

| Route ID | Movement | Origin -> Destination | Interpretation |
| --- | --- | --- | --- |
| `r_N_through` | through | `N -> S` | Major-road southbound through movement. |
| `r_N_left` | left | `N -> E` | Major-road left turn into the east branch. |
| `r_S_through` | through | `S -> N` | Major-road northbound through movement. |
| `r_S_right` | right | `S -> E` | Major-road right turn into the east branch. |
| `r_E_right` | right | `E -> N` | Minor-road right turn onto the major road. |
| `r_E_left` | left | `E -> S` | Minor-road left turn onto the major road. |

No movement to or from `W` is allowed. The east approach has no through movement.

## 7. Reference Path Model

Each legal movement `r` has a reference path:

```text
 P_r(s) = [x_r(s), y_r(s)], s in [0, L_r]
```

where `s` is path distance from the upstream approach entry.

Path construction rules:

1. Straight movements use lane-center straight segments between the corresponding inbound and outbound lane centers.
2. Turning movements use an inbound straight segment, a single low-speed circular-arc turn, and a downstream straight segment.
3. The arc is tangent to both the inbound and outbound lane-center directions.
4. The arc radius is `r_turn` unless a sensitivity run overrides it.
5. Paths are sampled every `ds = 0.25 m`.

The implementation may approximate circular arcs with polylines, but the stored route geometry must expose sampled points, heading, curvature proxy, and cumulative path distance. These are the geometric primitives used by conflict detection and arrival-time estimation.

## 8. Swept Area Model

For each route `r`, construct a swept area polygon:

```text
 S_r = buffer(P_r, w_veh / 2 + b_safe)
```

The buffer is a Minkowski-style lateral expansion around the sampled reference path. It represents the occupied route envelope of a passenger vehicle plus a safety margin. The first implementation can use a polyline buffer from a geometry library or a deterministic local buffer implementation; the method definition is independent of the implementation choice.

This is the critical upgrade from the current center-circle zone. A vehicle does not conflict with another vehicle merely because both are near `(0, 0)`; it conflicts when their intended movement envelopes overlap or when they share an upstream/downstream lane segment that imposes car-following or merging constraints.

## 9. Conflict Matrix And Conflict Types

The static route-conflict relation is:

```text
 M_ab = 1 if area(S_a intersection S_b) > A_min
        0 otherwise
```

for two routes `a` and `b`. The diagonal is treated as a same-route queue-following relation, not as a crossing conflict.

Each nonzero relation receives one conflict type:

| Type | Rule |
| --- | --- |
| `crossing` | The two route centerlines intersect with a large heading angle and neither route shares the same origin or destination lane. |
| `merging` | The routes have different origins and the same destination lane. |
| `diverging` | The routes share the same origin lane and have different destination lanes. |
| `queue_following` | The routes share the same lane and same direction for a nontrivial distance. |
| `overlap_turning` | The swept areas overlap inside the junction but the relation is not cleanly classified by the above rules. |

The classical T-intersection conflict-point count is used as a topology sanity check, not as a hard-coded matrix. A conventional all-movement T-intersection should expose the expected crossing, merging, and diverging structure, but our controller uses the generated movement-level matrix because swept areas depend on lane width, turn radius, and safety buffer.

Expected invariant examples:

- `r_N_through` and `r_S_through` should be geometrically compatible under the right-hand lane-offset convention.
- Routes with the same downstream lane, such as two movements exiting to `E`, should have a merging or queue-related constraint.
- Routes sharing the same inbound lane should not be released side-by-side from the same lane; their constraint is upstream diverging or queue-following rather than a center crossing.

## 10. Conflict-Zone Decomposition

For every conflicting route pair `(a, b)`, define one or more local conflict regions:

```text
 Z_ab = connected_components(S_a intersection S_b)
```

After filtering components with area below `A_min`, each component becomes a conflict zone:

```text
 z = {
   zone_id,
   route_ids,
   conflict_type,
   polygon,
   centroid,
   entry_distance_by_route,
   exit_distance_by_route
 }
```

If several pairwise components are spatially adjacent and represent the same physical region, they may be merged into a shared zone while preserving all participating route IDs. This gives the decision layer a set of route-level zones:

```text
 Z = {z_1, z_2, ..., z_K}
```

The current `center` circle remains only as a backward-compatible debug zone. It should not be used for the final method claims once this geometry layer is implemented.

## 11. Vehicle-To-Zone Mapping

At decision time `t`, each vehicle `i` has a route `r_i` or a route probability distribution. For a known route:

```text
 Z_i = {z in Z : r_i in z.route_ids}
```

For uncertain HDV intention:

```text
 P(z used by i) = sum over routes r containing z of P(r_i = r)
```

A vehicle enters the control problem if its path distance to the first relevant conflict zone is below `d_control` or if it is already inside any conflict-zone polygon.

## 12. Time Metrics

For a vehicle `i` and zone `z`, define:

```text
 tau_i^z_entry = predicted or observed time when i first enters z
 tau_i^z_exit  = predicted or observed time when i leaves z
```

These quantities support:

- priority-taking labels for HDV prediction,
- PET and TTCP diagnostics,
- vehicle conflict graph construction,
- coalition feasibility checks,
- passing-pattern evaluation.

Pairwise temporal conflict exists when the static geometry conflicts and:

```text
 |tau_i^z_entry - tau_j^z_entry| <= Delta_tau
```

or when one vehicle is predicted to enter before the other has exited plus a safety gap:

```text
 tau_i^z_entry < tau_j^z_exit + T_gap
```

The exact thresholds belong to the safety-metric configuration, but the geometry layer must provide the zone entry and exit distances needed to compute them.

## 13. Link To Coalition Game

The vehicle conflict graph is built from the geometry layer:

```text
 G_t = (V_t, E_t)
```

where `(i, j)` is an edge if the two vehicles share a route-level conflict zone and their predicted occupancy times overlap within the configured safety threshold.

Candidate coalitions are generated from connected components or dense local subgraphs of `G_t`. Non-conflicting vehicles may pass in parallel. This supports the paper's key method distinction:

```text
 coalition membership is induced by movement-level conflict geometry,
 not by arbitrary distance to the center of the intersection.
```

## 14. SUMO Implementation Contract

The SUMO network should remain a faithful implementation of the formal geometry, but the formal geometry is the source of truth for conflict reasoning.

Implementation rules:

1. Generate the T-junction from `active_approaches = ["N", "E", "S"]`.
2. Set lane width, speed limit, approach length, and turn radius from scenario config.
3. Keep SUMO internal links enabled so vehicles are simulated inside the intersection.
4. Export a geometry artifact containing route sampled paths, swept areas, static conflict matrix, and conflict zones.
5. Use the exported artifact for event extraction, label generation, conflict graph construction, and safety metrics.
6. Continue using SUMO right-of-way and HDV behavior models as traffic-generation mechanisms, not as the proposed controller.

The generated SUMO file names may remain backward-compatible during implementation, but experiment run IDs and reports should be scenario-prefixed with `t_junction`.

## 15. Validation Checks

The implementation will be accepted only if these checks pass:

1. Route set equals the six legal T-junction routes listed above.
2. No generated route uses `W` as an origin or destination.
3. Lane centers follow the right-hand traffic offset convention.
4. `r_N_through` and `r_S_through` are compatible under nominal geometry.
5. Same-destination route pairs expose merging or queue-related constraints.
6. Same-origin route pairs expose diverging or queue-following constraints.
7. The conflict matrix is symmetric.
8. Every nonzero conflict matrix entry maps to at least one conflict-zone component.
9. Every conflict-zone component has per-route entry and exit distances.
10. The old `center` circle can still be produced for debug runs, but final reports use route-level zones.

## 16. Experiment Variants

Use one main geometry and a small set of geometry sensitivities:

| Variant | Purpose | Changes |
| --- | --- | --- |
| `G0_nominal` | Main paper geometry | `w_lane=3.5`, `r_turn=10`, `b_safe=0.5`, `d_control=45`. |
| `G1_tight_turn` | Stress tight turning paths | `r_turn=8`. |
| `G2_wide_turn` | Test smoother geometry | `r_turn=12` or `15`. |
| `G3_conservative_buffer` | Safety-buffer sensitivity | `b_safe=0.75`. |

Do not make skewed, multi-lane, pedestrian, bicycle, or heavy-truck geometries part of the first main paper claim. They can be listed as limitations or future extensions.

## 17. Scope Boundary

Included now:

- orthogonal T-junction,
- single inbound and outbound lane per approach,
- six legal vehicle movements,
- route reference paths,
- swept-area conflict generation,
- conflict type classification,
- conflict-zone entry and exit distances,
- SUMO-compatible geometry export.

Excluded from this design cycle:

- multi-lane approaches,
- exclusive turn lanes,
- channelized islands,
- pedestrians and bicycles,
- heavy-truck design vehicles,
- skewed T-intersections,
- real INTERACTION map fitting.

These exclusions keep the first formal scene precise enough to publish and small enough to validate carefully.

## 18. Next Implementation Units

After this spec is reviewed, the implementation plan should be split into these units:

1. Add geometry parameters to `t_junction_scenario.json`.
2. Create a route-geometry module that samples reference paths.
3. Create swept-area and conflict-zone generation.
4. Export a reusable geometry artifact per scenario.
5. Replace center-circle event extraction with route-zone event extraction.
6. Update prediction labels and conflict graph construction to use route-level zones.
7. Add geometry tests for route legality, conflict matrix invariants, and zone entry distances.
8. Run a nominal T-junction smoke test and compare the route-zone event counts with the current center-zone debug output.

