from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from common import PROTOTYPE_ROOT


@dataclass(frozen=True)
class ExperimentJob:
    job_id: str
    group: str
    backend: str
    output_name: str
    params: dict


def _csv(values: list) -> str:
    return ",".join(str(value) for value in values)


def _command(job: ExperimentJob) -> str:
    params = job.params
    if job.backend == "label_sanity":
        return (
            "python sim/prototype/src/run_label_sanity_batch.py "
            f"--config {params['config_path']} "
            f"--seeds {_csv(params['seeds'])} "
            f"--volumes {_csv(params['volumes'])} "
            f"--penetrations {_csv(params['penetrations'])} "
            f"--duration {params['duration']} "
            f"--output-name {params['output_name']}"
        )
    if job.backend == "closed_loop":
        return (
            "python sim/prototype/src/run_closed_loop_batch.py "
            f"--config {params['config_path']} "
            f"--seeds {_csv(params['seeds'])} "
            f"--volumes {_csv(params['volumes'])} "
            f"--penetrations {_csv(params['penetrations'])} "
            f"--methods {_csv(params['methods'])} "
            f"--duration {params['duration']} "
            f"--control-radius-m {params['control_radius_m']} "
            f"--hold-speed-mps {params['hold_speed_mps']} "
            f"--risk-threshold {params['risk_threshold']} "
            f"--fairness-weight {params['fairness_weight']} "
            f"--max-release-count {params['max_release_count']} "
            f"--safe-arrival-gap-s {params['safe_arrival_gap_s']} "
            f"--near-conflict-pet-s {params['near_conflict_pet_s']} "
            f"--output-name {params['output_name']}"
        )
    raise ValueError(f"Unknown backend: {job.backend}")


def _expected_outputs(job: ExperimentJob) -> dict[str, str]:
    if job.backend == "label_sanity":
        prefix = job.output_name
        return {
            "summary_csv": str(PROTOTYPE_ROOT / "reports" / f"{prefix}_label_sanity_batch_summary.csv"),
            "summary_json": str(PROTOTYPE_ROOT / "reports" / f"{prefix}_label_sanity_batch_summary.json"),
        }
    if job.backend == "closed_loop":
        return {
            "summary_json": str(PROTOTYPE_ROOT / "reports" / job.output_name / "closed_loop_batch_summary.json"),
            "runs_csv": str(PROTOTYPE_ROOT / "reports" / job.output_name / "closed_loop_batch_runs.csv"),
            "aggregate_csv": str(PROTOTYPE_ROOT / "reports" / job.output_name / "closed_loop_batch_aggregate.csv"),
        }
    raise ValueError(f"Unknown backend: {job.backend}")


def _job_payload(job: ExperimentJob) -> dict:
    return {
        "job_id": job.job_id,
        "group": job.group,
        "backend": job.backend,
        "output_name": job.output_name,
        "params": job.params,
        "command": _command(job),
        "expected_outputs": _expected_outputs(job),
    }


def write_manifest(jobs: list[ExperimentJob], path: str | Path, status: str = "planned", results: list[dict] | None = None) -> Path:
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "job_count": len(jobs),
        "no_fabrication_note": "TBD result cells must be filled only from completed experiment outputs.",
        "jobs": [_job_payload(job) for job in jobs],
        "results": results or [],
    }
    manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path


def run_selected_jobs(
    jobs: list[ExperimentJob],
    selected_job_ids: list[str] | None = None,
    selected_groups: list[str] | None = None,
    label_runner=None,
    closed_loop_runner=None,
) -> list[dict]:
    from run_closed_loop_batch import run_batch as default_closed_loop_runner
    from run_label_sanity_batch import run_batch as default_label_runner

    label_runner = label_runner or default_label_runner
    closed_loop_runner = closed_loop_runner or default_closed_loop_runner
    job_id_filter = set(selected_job_ids or [])
    group_filter = set(selected_groups or [])
    results = []

    for job in jobs:
        if job_id_filter and job.job_id not in job_id_filter:
            continue
        if group_filter and job.group not in group_filter:
            continue
        if job.backend == "label_sanity":
            output = label_runner(**job.params)
        elif job.backend == "closed_loop":
            output = closed_loop_runner(**job.params)
        else:
            raise ValueError(f"Unknown backend: {job.backend}")
        results.append(
            {
                "job_id": job.job_id,
                "group": job.group,
                "backend": job.backend,
                "output_name": job.output_name,
                "status": "completed",
                "outputs": output,
            }
        )
    return results


def parse_csv_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def main() -> None:
    default_config = PROTOTYPE_ROOT / "config" / "t_junction_scenario.json"
    default_manifest = PROTOTYPE_ROOT / "reports" / "formal_experiment_queue_manifest.json"
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(default_config))
    parser.add_argument("--manifest", default=str(default_manifest))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run", default="", help="Comma-separated job ids to execute.")
    parser.add_argument("--run-group", default="", help="Comma-separated groups to execute, for example E1,E2,A1.")
    args = parser.parse_args()

    jobs = build_default_jobs(args.config)
    selected_job_ids = parse_csv_list(args.run)
    selected_groups = parse_csv_list(args.run_group)
    if args.dry_run or (not selected_job_ids and not selected_groups):
        manifest = write_manifest(jobs, args.manifest, status="planned")
        print(json.dumps({"manifest": str(manifest), "job_count": len(jobs), "status": "planned"}, indent=2))
        return

    results = run_selected_jobs(jobs, selected_job_ids=selected_job_ids, selected_groups=selected_groups)
    selected = [
        job
        for job in jobs
        if (not selected_job_ids or job.job_id in selected_job_ids)
        and (not selected_groups or job.group in selected_groups)
    ]
    manifest = write_manifest(selected, args.manifest, status="completed", results=results)
    print(json.dumps({"manifest": str(manifest), "job_count": len(selected), "status": "completed", "results": results}, indent=2))


def _closed_loop_params(
    *,
    config_path: str,
    output_name: str,
    seeds: list[int],
    volumes: list[str],
    penetrations: list[float],
    methods: list[str],
    duration: float = 120.0,
    fairness_weight: float = 0.15,
    max_release_count: int = 3,
    safe_arrival_gap_s: float = 1.2,
) -> dict:
    return {
        "config_path": config_path,
        "seeds": seeds,
        "volumes": volumes,
        "penetrations": penetrations,
        "methods": methods,
        "duration": duration,
        "control_radius_m": 45.0,
        "hold_speed_mps": 1.0,
        "risk_threshold": 0.7,
        "fairness_weight": fairness_weight,
        "max_release_count": max_release_count,
        "safe_arrival_gap_s": safe_arrival_gap_s,
        "near_conflict_pet_s": 1.5,
        "priority_model": None,
        "output_name": output_name,
    }


def build_default_jobs(config_path: str) -> list[ExperimentJob]:
    jobs = [
        ExperimentJob(
            job_id="E1_label_event_sanity",
            group="E1",
            backend="label_sanity",
            output_name="formal_e1_label_event_sanity",
            params={
                "config_path": config_path,
                "seeds": [1, 2, 3, 4, 5],
                "volumes": ["low", "medium", "high"],
                "penetrations": [0.2, 0.5, 0.8],
                "duration": 120.0,
                "max_runs": None,
                "output_name": "formal_e1_label_event_sanity",
            },
        ),
        ExperimentJob(
            job_id="E2_main_closed_loop_screening",
            group="E2",
            backend="closed_loop",
            output_name="formal_e2_main_screen_tj_routezone_seed1_5_lmh_pen20_50_80_d120",
            params=_closed_loop_params(
                config_path=config_path,
                output_name="formal_e2_main_screen_tj_routezone_seed1_5_lmh_pen20_50_80_d120",
                seeds=[1, 2, 3, 4, 5],
                volumes=["low", "medium", "high"],
                penetrations=[0.2, 0.5, 0.8],
                methods=["fcfs", "prediction_fcfs", "prediction_coalition"],
            ),
        ),
    ]

    for value in [0.0, 0.15, 0.3, 0.5]:
        token = str(value).replace(".", "_")
        output_name = f"ablation_a1_fairness_{token}_tj_seed1_5_mh_pen50_d120"
        jobs.append(
            ExperimentJob(
                job_id=f"A1_fairness_weight_{token}",
                group="A1",
                backend="closed_loop",
                output_name=output_name,
                params=_closed_loop_params(
                    config_path=config_path,
                    output_name=output_name,
                    seeds=[1, 2, 3, 4, 5],
                    volumes=["medium", "high"],
                    penetrations=[0.5],
                    methods=["prediction_coalition"],
                    fairness_weight=value,
                ),
            )
        )

    for value in [1, 2, 3]:
        output_name = f"ablation_a2_max_release_{value}_tj_seed1_5_mh_pen50_d120"
        jobs.append(
            ExperimentJob(
                job_id=f"A2_max_release_{value}",
                group="A2",
                backend="closed_loop",
                output_name=output_name,
                params=_closed_loop_params(
                    config_path=config_path,
                    output_name=output_name,
                    seeds=[1, 2, 3, 4, 5],
                    volumes=["medium", "high"],
                    penetrations=[0.5],
                    methods=["prediction_coalition"],
                    max_release_count=value,
                ),
            )
        )

    for value in [0.8, 1.2, 1.6]:
        token = str(value).replace(".", "_")
        output_name = f"ablation_a3_safe_gap_{token}_tj_seed1_5_mh_pen50_d120"
        jobs.append(
            ExperimentJob(
                job_id=f"A3_safe_gap_{token}",
                group="A3",
                backend="closed_loop",
                output_name=output_name,
                params=_closed_loop_params(
                    config_path=config_path,
                    output_name=output_name,
                    seeds=[1, 2, 3, 4, 5],
                    volumes=["medium", "high"],
                    penetrations=[0.5],
                    methods=["prediction_coalition"],
                    safe_arrival_gap_s=value,
                ),
            )
        )
    return jobs


if __name__ == "__main__":
    main()
