from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_prediction_dataset import build_prediction_dataset
from common import PROTOTYPE_ROOT, ensure_dirs, load_config, scenario_run_id, write_json
from run_label_sanity_batch import parse_csv_list


def build_batch_dataset(
    config_path: str,
    seeds: list[int],
    volumes: list[str],
    penetrations: list[float],
    history_s: float,
    sample_step_s: float,
    prediction_horizon_s: float,
    tolerance_s: float,
    high_confidence_only: bool,
    output_name: str,
) -> dict:
    ensure_dirs()
    cfg = load_config(config_path)
    out_dir = PROTOTYPE_ROOT / "datasets" / output_name
    out_dir.mkdir(parents=True, exist_ok=True)
    merged_jsonl = out_dir / "prediction_samples.jsonl"
    summaries = []
    total_samples = 0
    priority_positive = 0
    strict_positive = 0

    with merged_jsonl.open("w", encoding="utf-8") as merged:
        for seed in seeds:
            for volume in volumes:
                for penetration in penetrations:
                    rid = scenario_run_id(cfg, seed, volume, penetration)
                    summary = build_prediction_dataset(
                        run_id_value=rid,
                        history_s=history_s,
                        sample_step_s=sample_step_s,
                        prediction_horizon_s=prediction_horizon_s,
                        tolerance_s=tolerance_s,
                        high_confidence_only=high_confidence_only,
                    )
                    run_jsonl = Path(summary["output_jsonl"])
                    run_samples = 0
                    run_priority = 0
                    run_strict = 0
                    with run_jsonl.open("r", encoding="utf-8") as src:
                        for line in src:
                            merged.write(line)
                            run_samples += 1
                            obj = json.loads(line)
                            run_priority += int(obj["labels"]["hdv_takes_priority"])
                            run_strict += int(obj["labels"]["strict_non_yield"])
                    summary["priority_positive"] = run_priority
                    summary["strict_positive"] = run_strict
                    summaries.append(summary)
                    total_samples += run_samples
                    priority_positive += run_priority
                    strict_positive += run_strict

    merged_summary = {
        "output_name": output_name,
        "config_path": config_path,
        "run_count": len(summaries),
        "total_samples": total_samples,
        "hdv_takes_priority_count": priority_positive,
        "hdv_takes_priority_ratio": priority_positive / total_samples if total_samples else 0.0,
        "strict_non_yield_count": strict_positive,
        "strict_non_yield_ratio": strict_positive / total_samples if total_samples else 0.0,
        "history_s": history_s,
        "sample_step_s": sample_step_s,
        "prediction_horizon_s": prediction_horizon_s,
        "high_confidence_only": high_confidence_only,
        "merged_jsonl": str(merged_jsonl),
        "runs": summaries,
    }
    summary_file = out_dir / "prediction_dataset_batch_summary.json"
    write_json(summary_file, merged_summary)
    return merged_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(PROTOTYPE_ROOT / "config" / "stress_scenario.json"))
    parser.add_argument("--seeds", default="5,6")
    parser.add_argument("--volumes", default="low,medium,high")
    parser.add_argument("--penetrations", default="0.2,0.5,0.8")
    parser.add_argument("--history-s", type=float, default=3.0)
    parser.add_argument("--sample-step-s", type=float, default=0.5)
    parser.add_argument("--prediction-horizon-s", type=float, default=1.0)
    parser.add_argument("--tolerance-s", type=float, default=0.16)
    parser.add_argument("--high-confidence-only", action="store_true")
    parser.add_argument("--output-name", default="stress_seed5_6_priority_hc")
    args = parser.parse_args()
    summary = build_batch_dataset(
        config_path=args.config,
        seeds=parse_csv_list(args.seeds, int),
        volumes=parse_csv_list(args.volumes, str),
        penetrations=parse_csv_list(args.penetrations, float),
        history_s=args.history_s,
        sample_step_s=args.sample_step_s,
        prediction_horizon_s=args.prediction_horizon_s,
        tolerance_s=args.tolerance_s,
        high_confidence_only=args.high_confidence_only,
        output_name=args.output_name,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
