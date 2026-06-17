# Remote Execution Policy

Date: 2026-06-17

Purpose: protect the local laptop from heavy simulation/training load and keep formal experiment execution reproducible.

## Rule

From this point onward, all heavy experiment execution must run on the remote server, not on the local Codex laptop.

Local machine is allowed for:

- code editing,
- unit tests,
- manifest dry-runs,
- result aggregation from already-generated files,
- documentation and paper writing.

Remote server is required for:

- any SUMO batch larger than a tiny smoke test,
- all closed-loop formal experiments,
- selected-candidate re-screening,
- 300 s or 10-seed confirmatory runs,
- deep learning model training,
- robustness sweeps.

## Remote Runtime

Remote prototype directory:

```text
/public/home/xiaohei_0/hx/my_paper01/sim/prototype
```

Remote Python/SUMO environment:

```bash
conda activate sumoenv
```

or:

```bash
/public/home/xiaohei_0/conda38/bin/conda run -n sumoenv python ...
```

## Git Sync Policy

Before launching remote experiments:

1. Push the local branch to GitHub.
2. Pull or fetch the same branch on the remote server.
3. Run experiments from the remote prototype directory.
4. Copy back only summary artifacts needed for reporting, or record remote paths in a report.

Do not edit or commit generated `logs/`, `routes/`, `networks/`, `labels/`, `datasets/`, or `reports/` directories unless a specific small summary artifact is intentionally promoted into `docs/experiments/`.

## Next Remote Experiment

Selected candidate from J1:

```text
max_release_count = 3
safe_arrival_gap_s = 0.8
fairness_weight = 0.3
```

Run the selected-candidate E2-style re-screening remotely:

```bash
cd /public/home/xiaohei_0/hx/my_paper01/sim/prototype
/public/home/xiaohei_0/conda38/bin/conda run -n sumoenv python src/run_closed_loop_batch.py \
  --config config/t_junction_scenario.json \
  --seeds 1,2,3,4,5 \
  --volumes low,medium,high \
  --penetrations 0.2,0.5,0.8 \
  --methods fcfs,prediction_coalition \
  --duration 120 \
  --control-radius-m 45 \
  --fairness-weight 0.3 \
  --max-release-count 3 \
  --safe-arrival-gap-s 0.8 \
  --near-conflict-pet-s 1.5 \
  --output-name formal_rescreen_selected_mr3_gap08_fw03_seed1_5_lmh_pen20_50_80_d120
```

Expected output directory:

```text
/public/home/xiaohei_0/hx/my_paper01/sim/prototype/reports/formal_rescreen_selected_mr3_gap08_fw03_seed1_5_lmh_pen20_50_80_d120
```

## Local Safety Note

Do not run the command above locally. The local laptop has already shown significant slowdown during 120 s screening batches.
