# E1 Label And Event Sanity Report

Date: 2026-06-17

Scenario: T-junction route-zone geometry, mixed CAV/HDV traffic, unsignalized intersection.

Command:

```powershell
python sim/prototype/src/run_formal_experiment_queue.py --run E1_label_event_sanity
```

Generated artifacts:

- `sim/prototype/reports/formal_e1_label_event_sanity_label_sanity_batch_summary.csv`
- `sim/prototype/reports/formal_e1_label_event_sanity_label_sanity_batch_summary.json`
- `sim/prototype/reports/formal_experiment_queue_manifest.json`

These artifacts are local generated outputs and are intentionally ignored by Git. This document records only verified aggregate values from that completed run.

## Overall Result

| Metric | Value |
| --- | ---: |
| Runs | 45 |
| Vehicles | 2888 |
| Route-zone events | 3374 |
| Yield labels | 1193 |
| HDV takes-priority labels | 615 |
| HDV yields-by-priority labels | 578 |
| Non-yield labels | 223 |
| Yield labels | 970 |
| High-confidence labels | 1191 |
| Low-confidence labels | 2 |
| Non-yield ratio | 0.1869 |
| HDV takes-priority ratio | 0.5155 |

## By Demand Level

| Volume | Runs | Vehicles | Route-zone events | Yield labels | High-confidence labels | Low-confidence labels |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| low | 15 | 675 | 1019 | 327 | 325 | 2 |
| medium | 15 | 1005 | 1158 | 417 | 417 | 0 |
| high | 15 | 1208 | 1197 | 449 | 449 | 0 |

## By CAV Penetration

| CAV penetration | Runs | Vehicles | Route-zone events | Yield labels | HDV takes priority | Yield | Non-yield |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.2 | 15 | 977 | 1140 | 590 | 300 | 473 | 117 |
| 0.5 | 15 | 962 | 1159 | 414 | 221 | 344 | 70 |
| 0.8 | 15 | 949 | 1075 | 189 | 94 | 153 | 36 |

## Sparse Runs

The lowest-label settings were mostly high-CAV-penetration runs, which is expected because the label task is HDV-priority oriented.

| Run | Volume | CAV penetration | Vehicles | Events | Labels |
| --- | --- | ---: | ---: | ---: | ---: |
| `t_junction_unsignalized_stress_p0_seed3_low_pen80` | low | 0.8 | 45 | 55 | 1 |
| `t_junction_unsignalized_stress_p0_seed2_high_pen80` | high | 0.8 | 73 | 61 | 2 |
| `t_junction_unsignalized_stress_p0_seed2_medium_pen80` | medium | 0.8 | 62 | 60 | 2 |
| `t_junction_unsignalized_stress_p0_seed2_high_pen50` | high | 0.5 | 79 | 73 | 3 |
| `t_junction_unsignalized_stress_p0_seed1_low_pen20` | low | 0.2 | 45 | 47 | 4 |

## Interpretation

The E1 sanity sweep passes the minimum data-validity check:

- Route-zone event extraction is active across all 45 runs.
- The total label count is large enough to continue with E2 closed-loop screening.
- Medium and high demand settings produce stable label totals.
- High CAV penetration produces fewer HDV-priority labels, so learned HDV-priority claims should be made carefully there.
- The E2 main closed-loop comparison can proceed under the planned 5-seed, 3-volume, 3-penetration screening protocol.

No closed-loop performance claim is made by this report.
