from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))


class FormalExperimentQueueTest(unittest.TestCase):
    def test_label_batch_output_name_paths_are_isolated(self) -> None:
        from run_label_sanity_batch import label_batch_output_paths

        paths = label_batch_output_paths("formal_e1_label_sanity")

        self.assertEqual(paths["summary_csv"].name, "formal_e1_label_sanity_label_sanity_batch_summary.csv")
        self.assertEqual(paths["summary_json"].name, "formal_e1_label_sanity_label_sanity_batch_summary.json")

    def test_build_default_queue_contains_planned_formal_jobs(self) -> None:
        from run_formal_experiment_queue import build_default_jobs

        jobs = build_default_jobs(config_path="cfg.json")
        job_ids = [job.job_id for job in jobs]

        self.assertEqual(
            job_ids,
            [
                "E1_label_event_sanity",
                "E2_main_closed_loop_screening",
                "A1_fairness_weight_0_0",
                "A1_fairness_weight_0_15",
                "A1_fairness_weight_0_3",
                "A1_fairness_weight_0_5",
                "A2_max_release_1",
                "A2_max_release_2",
                "A2_max_release_3",
                "A3_safe_gap_0_8",
                "A3_safe_gap_1_2",
                "A3_safe_gap_1_6",
                "J1_mr2_gap0_8_fw0_15",
                "J1_mr2_gap0_8_fw0_3",
                "J1_mr2_gap1_2_fw0_15",
                "J1_mr2_gap1_2_fw0_3",
                "J1_mr3_gap0_8_fw0_15",
                "J1_mr3_gap0_8_fw0_3",
                "J1_mr3_gap1_2_fw0_15",
                "J1_mr3_gap1_2_fw0_3",
            ],
        )

    def test_build_default_queue_contains_joint_tuning_jobs(self) -> None:
        from run_formal_experiment_queue import build_default_jobs

        jobs = [job for job in build_default_jobs(config_path="cfg.json") if job.group == "J1"]
        job_ids = [job.job_id for job in jobs]

        self.assertEqual(
            job_ids,
            [
                "J1_mr2_gap0_8_fw0_15",
                "J1_mr2_gap0_8_fw0_3",
                "J1_mr2_gap1_2_fw0_15",
                "J1_mr2_gap1_2_fw0_3",
                "J1_mr3_gap0_8_fw0_15",
                "J1_mr3_gap0_8_fw0_3",
                "J1_mr3_gap1_2_fw0_15",
                "J1_mr3_gap1_2_fw0_3",
            ],
        )
        self.assertEqual(jobs[0].params["max_release_count"], 2)
        self.assertEqual(jobs[0].params["safe_arrival_gap_s"], 0.8)
        self.assertEqual(jobs[0].params["fairness_weight"], 0.15)
        self.assertEqual(jobs[0].params["cav_waiting_tiebreaker_weight"], 0.0)
        self.assertEqual(jobs[0].params["volumes"], ["medium", "high"])
        self.assertEqual(jobs[0].params["penetrations"], [0.5])

    def test_write_manifest_records_commands_without_results(self) -> None:
        from run_formal_experiment_queue import build_default_jobs, write_manifest

        with tempfile.TemporaryDirectory() as tmp:
            manifest = write_manifest(build_default_jobs("cfg.json")[:2], Path(tmp) / "manifest.json")
            payload = json.loads(manifest.read_text(encoding="utf-8"))

        self.assertEqual(payload["status"], "planned")
        self.assertEqual(payload["job_count"], 2)
        self.assertEqual(payload["jobs"][0]["job_id"], "E1_label_event_sanity")
        self.assertIn("--cav-waiting-tiebreaker-weight 0.0", payload["jobs"][1]["command"])
        self.assertIn("TBD", payload["no_fabrication_note"])

    def test_run_selected_jobs_uses_backend_functions(self) -> None:
        from run_formal_experiment_queue import build_default_jobs, run_selected_jobs

        jobs = build_default_jobs("cfg.json")[:2]
        calls = []

        def fake_label(**kwargs):
            calls.append(("label", kwargs["output_name"]))
            return {"summary_json": "label.json"}

        def fake_closed_loop(**kwargs):
            calls.append(("closed", kwargs["output_name"]))
            return {"summary": "closed.json"}

        results = run_selected_jobs(
            jobs,
            selected_job_ids=["E1_label_event_sanity", "E2_main_closed_loop_screening"],
            label_runner=fake_label,
            closed_loop_runner=fake_closed_loop,
        )

        self.assertEqual(
            calls,
            [
                ("label", "formal_e1_label_event_sanity"),
                ("closed", "formal_e2_main_screen_tj_routezone_seed1_5_lmh_pen20_50_80_d120"),
            ],
        )
        self.assertEqual([item["status"] for item in results], ["completed", "completed"])


if __name__ == "__main__":
    unittest.main()
