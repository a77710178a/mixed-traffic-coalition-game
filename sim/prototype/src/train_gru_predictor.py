from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from common import PROTOTYPE_ROOT, ensure_dirs, write_csv, write_json
from train_prediction_baselines import binary_metrics, seed_from_run_id


STATE_FEATURES = ["x", "y", "speed", "acceleration", "heading", "distance_to_center"]


def load_jsonl(path: Path) -> list[dict]:
    samples = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
    return samples


def split_samples(samples: list[dict], train_seeds: set[int], test_seeds: set[int]) -> tuple[list[dict], list[dict]]:
    train = [sample for sample in samples if seed_from_run_id(sample["run_id"]) in train_seeds]
    test = [sample for sample in samples if seed_from_run_id(sample["run_id"]) in test_seeds]
    if not train or not test:
        raise ValueError("Train/test split produced an empty split. Check seed arguments.")
    return train, test


def history_tensor(sample: dict) -> np.ndarray:
    hdv = [[float(row[name]) for name in STATE_FEATURES] for row in sample["hdv_history"]]
    other = [[float(row[name]) for name in STATE_FEATURES] for row in sample["other_history"]]
    return np.asarray([h + o for h, o in zip(hdv, other)], dtype=np.float32)


def make_arrays(samples: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    x = np.stack([history_tensor(sample) for sample in samples], axis=0)
    y = np.asarray([sample["labels"]["hdv_takes_priority"] for sample in samples], dtype=np.float32)
    return x, y


def standardize_sequence(train_x: np.ndarray, test_x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mean = train_x.reshape(-1, train_x.shape[-1]).mean(axis=0)
    std = train_x.reshape(-1, train_x.shape[-1]).std(axis=0)
    std[std < 1e-8] = 1.0
    return (train_x - mean) / std, (test_x - mean) / std, mean, std


class SequenceDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray) -> None:
        self.x = torch.from_numpy(x.astype(np.float32))
        self.y = torch.from_numpy(y.astype(np.float32))

    def __len__(self) -> int:
        return int(self.y.shape[0])

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.x[index], self.y[index]


class GRUPredictor(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, num_layers: int, dropout: float) -> None:
        super().__init__()
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        _out, hidden = self.gru(x)
        last = hidden[-1]
        return self.head(last).squeeze(-1)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train_model(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    test_y: np.ndarray,
    hidden_dim: int,
    num_layers: int,
    dropout: float,
    batch_size: int,
    epochs: int,
    lr: float,
    weight_decay: float,
    device: torch.device,
) -> tuple[GRUPredictor, list[dict], np.ndarray]:
    model = GRUPredictor(train_x.shape[-1], hidden_dim, num_layers, dropout).to(device)
    loader = DataLoader(SequenceDataset(train_x, train_y), batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = nn.BCEWithLogitsLoss()
    history = []

    test_tensor = torch.from_numpy(test_x.astype(np.float32)).to(device)
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        total_count = 0
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            logits = model(batch_x)
            loss = loss_fn(logits, batch_y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()
            total_loss += float(loss.item()) * int(batch_y.shape[0])
            total_count += int(batch_y.shape[0])
        if epoch == 1 or epoch % 10 == 0 or epoch == epochs:
            model.eval()
            with torch.no_grad():
                probs = torch.sigmoid(model(test_tensor)).detach().cpu().numpy()
            metrics = binary_metrics(test_y.astype(np.float64), probs.astype(np.float64))
            history.append({
                "epoch": epoch,
                "train_loss": total_loss / max(1, total_count),
                "test_f1": metrics["f1"],
                "test_auc": metrics["auc"],
            })

    model.eval()
    with torch.no_grad():
        probs = torch.sigmoid(model(test_tensor)).detach().cpu().numpy()
    return model, history, probs


def run_training(
    dataset_path: Path,
    train_seeds: set[int],
    test_seeds: set[int],
    hidden_dim: int,
    num_layers: int,
    dropout: float,
    batch_size: int,
    epochs: int,
    lr: float,
    weight_decay: float,
    seed: int,
) -> dict:
    set_seed(seed)
    samples = load_jsonl(dataset_path)
    train_samples, test_samples = split_samples(samples, train_seeds, test_seeds)
    train_x, train_y = make_arrays(train_samples)
    test_x, test_y = make_arrays(test_samples)
    train_x, test_x, mean, std = standardize_sequence(train_x, test_x)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _model, history, test_prob = train_model(
        train_x=train_x,
        train_y=train_y,
        test_x=test_x,
        test_y=test_y,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        dropout=dropout,
        batch_size=batch_size,
        epochs=epochs,
        lr=lr,
        weight_decay=weight_decay,
        device=device,
    )
    metrics = binary_metrics(test_y.astype(np.float64), test_prob.astype(np.float64))
    return {
        "dataset_path": str(dataset_path),
        "train_seeds": sorted(train_seeds),
        "test_seeds": sorted(test_seeds),
        "train_samples": len(train_samples),
        "test_samples": len(test_samples),
        "train_positive_ratio": float(train_y.mean()),
        "test_positive_ratio": float(test_y.mean()),
        "device": str(device),
        "model": {
            "type": "gru_only",
            "input_dim": int(train_x.shape[-1]),
            "sequence_length": int(train_x.shape[1]),
            "hidden_dim": hidden_dim,
            "num_layers": num_layers,
            "dropout": dropout,
        },
        "training": {
            "batch_size": batch_size,
            "epochs": epochs,
            "lr": lr,
            "weight_decay": weight_decay,
            "seed": seed,
            "history": history,
        },
        "metrics": metrics,
        "feature_names": [f"hdv_{name}" for name in STATE_FEATURES] + [f"other_{name}" for name in STATE_FEATURES],
        "standardization_mean": mean.tolist(),
        "standardization_std": std.tolist(),
    }


def write_metric_csv(summary: dict, output_csv: Path) -> None:
    row = {"method": "gru_only"}
    row.update(summary["metrics"])
    write_csv(
        output_csv,
        [row],
        ["method", "accuracy", "precision", "recall", "f1", "auc", "tp", "tn", "fp", "fn"],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        default=str(PROTOTYPE_ROOT / "datasets" / "stress_seed5_6_priority_hc_h3" / "prediction_samples.jsonl"),
    )
    parser.add_argument("--train-seeds", default="5")
    parser.add_argument("--test-seeds", default="6")
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--num-layers", type=int, default=1)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output-name", default="gru_seed5_train_seed6_test_h3")
    args = parser.parse_args()

    ensure_dirs()
    output_dir = PROTOTYPE_ROOT / "reports" / args.output_name
    output_dir.mkdir(parents=True, exist_ok=True)
    train_seeds = {int(seed.strip()) for seed in args.train_seeds.split(",") if seed.strip()}
    test_seeds = {int(seed.strip()) for seed in args.test_seeds.split(",") if seed.strip()}
    summary = run_training(
        dataset_path=Path(args.dataset),
        train_seeds=train_seeds,
        test_seeds=test_seeds,
        hidden_dim=args.hidden_dim,
        num_layers=args.num_layers,
        dropout=args.dropout,
        batch_size=args.batch_size,
        epochs=args.epochs,
        lr=args.lr,
        weight_decay=args.weight_decay,
        seed=args.seed,
    )
    summary_file = output_dir / "gru_prediction_summary.json"
    metrics_file = output_dir / "gru_prediction_metrics.csv"
    write_json(summary_file, summary)
    write_metric_csv(summary, metrics_file)
    print(json.dumps({"summary": str(summary_file), "metrics": str(metrics_file), **summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
