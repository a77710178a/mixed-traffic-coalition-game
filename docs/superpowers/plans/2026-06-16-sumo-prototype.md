# SUMO Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable SUMO data-generation loop for the mixed-traffic unsignalized-intersection paper.

**Architecture:** Keep this prototype independent from the older remote `hx/sim_platform` project while reusing its proven SUMO/TraCI style. The first milestone creates a four-leg unsignalized intersection, generates mixed CAV/HDV route files, logs per-step vehicle states, extracts conflict-zone events, and derives HDV yield/non-yield labels.

**Tech Stack:** Python 3.9, SUMO 1.23.1, TraCI, sumolib, CSV/JSON artifacts, remote conda environment `sumoenv`.

---

### Task 1: Local Prototype Skeleton

**Files:**
- Create: `sim/prototype/README.md`
- Create: `sim/prototype/config/default_scenario.json`
- Create: `sim/prototype/src/common.py`

- [x] **Step 1:** Create the directory layout for network files, route files, scripts, logs, labels, reports, and source modules.
- [x] **Step 2:** Add a scenario JSON containing intersection geometry, demand settings, CAV penetration, HDV behavior mix, and label thresholds.
- [x] **Step 3:** Add shared helpers for paths, JSON loading, deterministic randomness, and CSV writing.

### Task 2: SUMO Network And Routes

**Files:**
- Create: `sim/prototype/src/generate_network.py`
- Create: `sim/prototype/src/generate_routes.py`

- [x] **Step 1:** Generate four-leg node, edge, connection, and SUMO config XML files.
- [x] **Step 2:** Generate route XML with CAV/HDV vehicle types, left/through/right movement routes, random seeds, traffic volume, and penetration settings.
- [x] **Step 3:** Verify the network with remote `netconvert` in `sumoenv`.

### Task 3: TraCI Logger

**Files:**
- Create: `sim/prototype/src/run_sumo.py`

- [x] **Step 1:** Start SUMO headlessly using the generated config.
- [x] **Step 2:** Log per-step vehicle state, including position, speed, acceleration, lane, route, movement, and distance to conflict center.
- [x] **Step 3:** Emit `vehicle_states.csv` and a compact run metadata JSON.

### Task 4: Conflict Events And Labels

**Files:**
- Create: `sim/prototype/src/extract_conflict_events.py`
- Create: `sim/prototype/src/generate_yield_labels.py`

- [x] **Step 1:** Convert vehicle-state logs into conflict-zone entry/exit events.
- [x] **Step 2:** Pair HDVs with conflicting vehicles in a shared zone.
- [x] **Step 3:** Derive `non_yield=1/0` labels using crossing order and pre-zone deceleration.
- [x] **Step 4:** Write label summary counts for sanity checking.

### Task 5: Remote Smoke Test

**Files:**
- Modify: remote `/public/home/xiaohei_0/hx/my_paper01`

- [x] **Step 1:** Upload the prototype to the remote paper directory.
- [x] **Step 2:** Run network generation, route generation, SUMO logging, event extraction, and label generation under `sumoenv`.
- [x] **Step 3:** Inspect output file existence and label distribution.

