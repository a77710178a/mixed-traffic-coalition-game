from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

import numpy as np

from common import PROTOTYPE_ROOT, ensure_dirs, write_csv, write_json


EDGE_FEATURES = [
    "relative_distance",
    "relative_speed_hdv_minus_other",
    "distance_to_center_hdv_minus_other",
    "estimated_ttcp_hdv",
    "estimated_ttcp_other",
    "estimated_ttcp_diff_hdv_minus_other",
    "same_movement",
    "other_is_cav",
]

STATE_FEATURES = [
    "x",
    "y",
    "speed",
    "acceleration",
    "heading",
    "distance_to_center",
]


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def seed_from_run_id(run_id: str) -> int:
    match = re.search(r"(?:^|_)seed(\d+)(?:_|$)", run_id)
    if match is None:
        raise ValueError(f"Cannot parse seed from run_id: {run_id}")
    return int(match.group(1))


def feature_vector(sample: dict) -> list[float]:
    edge = sample["edge_features"]
    hdv_state = sample["hdv_context"]["state_at_sample_time"]
    other_state = sample["other_context"]["state_at_sample_time"]
    features = [float(edge[name]) for name in EDGE_FEATURES]
    features.extend(float(hdv_state[name]) for name in STATE_FEATURES)
    features.extend(float(other_state[name]) for name in STATE_FEATURES)
    return features


def make_matrix(samples: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray([feature_vector(sample) for sample in samples], dtype=np.float64)
    y = np.asarray([sample["labels"]["hdv_takes_priority"] for sample in samples], dtype=np.float64)
    return x, y


def sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(z, -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-z))


def standardize(train_x: np.ndarray, test_x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mean = train_x.mean(axis=0)
    std = train_x.std(axis=0)
    std[std < 1e-8] = 1.0
    return (train_x - mean) / std, (test_x - mean) / std, mean, std


def train_logistic_regression(
    train_x: np.ndarray,
    train_y: np.ndarray,
    lr: float,
    epochs: int,
    l2: float,
) -> tuple[np.ndarray, float, list[dict]]:
    weights = np.zeros(train_x.shape[1], dtype=np.float64)
    bias = 0.0
    history = []
    n = max(1, len(train_y))
    for epoch in range(1, epochs + 1):
        probs = sigmoid(train_x @ weights + bias)
        error = probs - train_y
        grad_w = (train_x.T @ error) / n + l2 * weights
        grad_b = float(error.mean())
        weights -= lr * grad_w
        bias -= lr * grad_b
        if epoch == 1 or epoch % 100 == 0 or epoch == epochs:
            eps = 1e-12
            loss = -np.mean(train_y * np.log(probs + eps) + (1 - train_y) * np.log(1 - probs + eps))
            loss += 0.5 * l2 * float(np.dot(weights, weights))
            history.append({"epoch": epoch, "loss": float(loss)})
    return weights, bias, history


def roc_auc_score(y_true: np.ndarray, y_score: np.ndarray) -> float:
    positives = y_score[y_true == 1]
    negatives = y_score[y_true == 0]
    if len(positives) == 0 or len(negatives) == 0:
        return 0.5
    order = np.argsort(y_score)
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(1, len(y_score) + 1, dtype=np.float64)
    pos_ranks = ranks[y_true == 1].sum()
    return float((pos_ranks - len(positives) * (len(positives) + 1) / 2) / (len(positives) * len(negatives)))


def binary_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> dict:
    y_pred = (y_prob >= threshold).astype(np.int64)
    y_int = y_true.astype(np.int64)
    tp = int(((y_pred == 1) & (y_int == 1)).sum())
    tn = int(((y_pred == 0) & (y_int == 0)).sum())
    fp = int(((y_pred == 1) & (y_int == 0)).sum())
    fn = int(((y_pred == 0) & (y_int == 1)).sum())
    accuracy = (tp + tn) / max(1, len(y_int))
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "auc": roc_auc_score(y_int, y_prob),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def constant_arrival_probability(samples: list[dict]) -> np.ndarray:
    probs = []
    for sample in samples:
        diff = float(sample["edge_features"]["estimated_ttcp_diff_hdv_minus_other"])
        # Negative diff means the HDV is predicted to arrive first.
        probs.append(1.0 / (1.0 + math.exp(max(-40.0, min(40.0, diff)))))
    return np.asarray(probs, dtype=np.float64)


def split_samples(samples: list[dict], train_seeds: set[int], test_seeds: set[int]) -> tuple[list[dict], list[dict]]:
    train = [sample for sample in samples if seed_from_run_id(sample["run_id"]) in train_seeds]
    test = [sample for sample in samples if seed_from_run_id(sample["run_id"]) in test_seeds]
    if not train or not test:
        raise ValueError("Train/test split produced an empty split. Check seed arguments.")
    return train, test


def train_and_evaluate(
    dataset_path: Path,
    train_seeds: set[int],
    test_seeds: set[int],
    lr: float,
    epochs: int,
    l2: float,
) -> dict:
    samples = load_jsonl(dataset_path)
    train_samples, test_samples = split_samples(samples, train_seeds, test_seeds)
    train_x, train_y = make_matrix(train_samples)
    test_x, test_y = make_matrix(test_samples)
    train_x_std, test_x_std, mean, std = standardize(train_x, test_x)

    weights, bias, history = train_logistic_regression(train_x_std, train_y, lr=lr, epochs=epochs, l2=l2)
    logistic_test_prob = sigmoid(test_x_std @ weights + bias)
    constant_test_prob = constant_arrival_probability(test_samples)

    return {
        "dataset_path": str(dataset_path),
        "train_seeds": sorted(train_seeds),
        "test_seeds": sorted(test_seeds),
        "train_samples": len(train_samples),
        "test_samples": len(test_samples),
        "train_positive_ratio": float(train_y.mean()),
        "test_positive_ratio": float(test_y.mean()),
        "methods": {
            "constant_arrival": binary_metrics(test_y, constant_test_prob),
            "logistic_regression": binary_metrics(test_y, logistic_test_prob),
        },
        "training": {
            "lr": lr,
            "epochs": epochs,
            "l2": l2,
            "loss_history": history,
        },
        "feature_names": EDGE_FEATURES
        + [f"hdv_{name}" for name in STATE_FEATURES]
        + [f"other_{name}" for name in STATE_FEATURES],
        "logistic_weights": weights.tolist(),
        "logistic_bias": bias,
        "standardization_mean": mean.tolist(),
        "standardization_std": std.tolist(),
    }


def write_result_table(summary: dict, output_csv: Path) -> None:
    rows = []
    for method, metrics in summary["methods"].items():
        row = {"method": method}
        row.update({key: value for key, value in metrics.items() if key in ["accuracy", "precision", "recall", "f1", "auc"]})
        row.update({key: value for key, value in metrics.items() if key in ["tp", "tn", "fp", "fn"]})
        rows.append(row)
    write_csv(
        output_csv,
        rows,
        ["method", "accuracy", "precision", "recall", "f1", "auc", "tp", "tn", "fp", "fn"],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        default=str(PROTOTYPE_ROOT / "datasets" / "stress_seed5_6_priority_hc" / "prediction_samples.jsonl"),
    )
    parser.add_argument("--train-seeds", default="5")
    parser.add_argument("--test-seeds", default="6")
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--epochs", type=int, default=1000)
    parser.add_argument("--l2", type=float, default=1e-3)
    parser.add_argument("--output-name", default="baseline_seed5_train_seed6_test")
    args = parser.parse_args()

    ensure_dirs()
    output_dir = PROTOTYPE_ROOT / "reports" / args.output_name
    output_dir.mkdir(parents=True, exist_ok=True)
    train_seeds = {int(seed.strip()) for seed in args.train_seeds.split(",") if seed.strip()}
    test_seeds = {int(seed.strip()) for seed in args.test_seeds.split(",") if seed.strip()}
    summary = train_and_evaluate(
        dataset_path=Path(args.dataset),
        train_seeds=train_seeds,
        test_seeds=test_seeds,
        lr=args.lr,
        epochs=args.epochs,
        l2=args.l2,
    )
    summary_file = output_dir / "prediction_baseline_summary.json"
    table_file = output_dir / "prediction_baseline_metrics.csv"
    write_json(summary_file, summary)
    write_result_table(summary, table_file)
    print(json.dumps({"summary": str(summary_file), "metrics": str(table_file), **summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
