# Adaptive Gate Confirmatory Failure Cases

Date: 2026-06-18

Source: `docs/experiments/formal_confirm_adaptive_gate_300s_report_20260618.md`

This note isolates the lowest-PET C1 runs so the paper can state where the adaptive gate is still weak.

## Selection Rule

Use the worst per-run PET cases from the 10-seed confirmatory batch.

These cases are not the aggregate result. They are the runs that matter most for limitation analysis.

## Worst Cases

| Seed | Volume | Penetration | Adaptive min PET | FCFS min PET | Adaptive near conflicts | FCFS near conflicts | Adaptive travel time | FCFS travel time | Adaptive throughput | FCFS throughput |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | medium | 0.5 | 1.00 | 1.10 | 3 | 4 | 138.09 | 144.69 | 38 | 39 |
| 4 | medium | 0.8 | 1.00 | 1.10 | 1 | 2 | 156.34 | 154.55 | 32 | 32 |
| 7 | medium | 0.5 | 1.00 | 0.90 | 5 | 5 | 147.83 | 147.47 | 32 | 34 |
| 4 | high | 0.8 | 1.10 | 1.00 | 2 | 2 | 160.25 | 155.73 | 35 | 35 |
| 7 | high | 0.5 | 1.10 | 1.10 | 4 | 4 | 152.29 | 156.00 | 36 | 36 |
| 5 | medium | 0.8 | 1.10 | 1.20 | 2 | 1 | 163.60 | 156.50 | 27 | 30 |
| 3 | high | 0.5 | 1.20 | 1.20 | 2 | 2 | 158.41 | 163.84 | 29 | 30 |
| 9 | medium | 0.5 | 1.60 | 1.40 | 0 | 1 | 153.21 | 154.83 | 32 | 35 |

## What These Cases Suggest

1. The low-PET cases are not all high-demand cases. Some occur at medium demand and 50% CAV penetration.
2. The adaptive gate can still reduce near conflicts in several low-PET runs, so near-conflict count alone is not enough to guarantee a large PET margin.
3. The hardest cases often have only one or two vehicles in the critical release window, which suggests the issue is local release timing rather than system-wide overload.
4. The current gate is better framed as an aggregate safety-efficiency improvement than a per-run PET guarantee.

## Paper Use

Use this note in the limitations subsection:

```text
The adaptive gate improves aggregate PET and near-conflict metrics, but several runs still produce low individual PET values around 1.0 s. These cases appear at both medium and high demand and are tied to local release timing rather than only to global saturation.
```

Do not use this note to weaken the main claim beyond the actual evidence. It is a limitation note, not a rejection of the method.
