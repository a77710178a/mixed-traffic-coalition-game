from __future__ import annotations

import argparse
import copy
import json
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from common import PROTOTYPE_ROOT, ensure_dirs, write_csv, write_json
from train_prediction_baselines import EDGE_FEATURES, binary_metrics, seed_from_run_id
from train_gru_predictor import STATE_FEATURES, load_jsonl, set_seed


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


def edge_vector(sample: dict) -> np.ndarray:
    edge = sample["edge_features"]
    return np.asarray([float(edge[name]) for name in EDGE_FEATURES], dtype=np.float32)


def make_arrays(samples: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    seq = np.stack([history_tensor(sample) for sample in samples], axis=0)
    edge = np.stack([edge_vector(sample) for sample in samples], axis=0)
    y = np.asarray([sample["labels"]["hdv_takes_priority"] for sample in samples], dtype=np.float32)
    return seq, edge, y


def standardize_sequence(train_x: np.ndarray, test_x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mean = train_x.reshape(-1, train_x.shape[-1]).mean(axis=0)
    std = train_x.reshape(-1, train_x.shape[-1]).std(axis=0)
    std[std < 1e-8] = 1.0
    return (train_x - mean) / std, (test_x - mean) / std, mean, std


def standardize_matrix(train_x: np.ndarray, test_x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mean = train_x.mean(axis=0)
    std = train_x.std(axis=0)
    std[std < 1e-8] = 1.0
    return (train_x - mean) / std, (test_x - mean) / std, mean, std


class SequenceEdgeDataset(Dataset):
    def __init__(self, seq_x: np.ndarray, edge_x: np.ndarray, y: np.ndarray) -> None:
        self.seq_x = torch.from_numpy(seq_x.astype(np.float32))
        self.edge_x = torch.from_numpy(edge_x.astype(np.float32))
        self.y = torch.from_numpy(y.astype(np.float32))

    def __len__(self) -> int:
        return int(self.y.shape[0])

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.seq_x[index], self.edge_x[index], self.y[index]


class GRUEdgePredictor(nn.Module):
    def __init__(
        self,
        seq_input_dim: int,
        edge_input_dim: int,
        hidden_dim: int,
        edge_dim: int,
        num_layers: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.gru = nn.GRU(
            input_size=seq_input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.edge_encoder = nn.Sequential(
            nn.Linear(edge_input_dim, edge_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(edge_dim, edge_dim),
            nn.ReLU(),
        )
        self.head = nn.Sequential(
            nn.Linear(hidden_dim + edge_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, seq_x: torch.Tensor, edge_x: torch.Tensor) -> torch.Tensor:
        _out, hidden = self.gru(seq_x)
        hist = hidden[-1]
        edge = self.edge_encoder(edge_x)
        return self.head(torch.cat([hist, edge], dim=-1)).squeeze(-1)


def train_model(
    train_seq: np.ndarray,
    train_edge: np.ndarray,
    train_y: np.ndarray,
    test_seq: np.ndarray,
    test_edge: np.ndarray,
    test_y: np.ndarray,
    hidden_dim: int,
    edge_dim: int,
    num_layers: int,
    dropout: float,
    batch_size: int,
    epochs: int,
    lr: float,
    weight_decay: float,
    device: torch.device,
) -> tuple[GRUEdgePredictor, list[dict], np.ndarray]:
    model = GRUEdgePredictor(
        seq_input_dim=train_seq.shape[-1],
        edge_input_dim=train_edge.shape[-1],
        hidden_dim=hidden_dim,
        edge_dim=edge_dim,
        num_layers=num_layers,
        dropout=dropout,
    ).to(device)
    loader = DataLoader(SequenceEdgeDataset(train_seq, train_edge, train_y), batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = nn.BCEWithLogitsLoss()
    history = []
    best_state = None
    best_f1 = -1.0
    test_seq_tensor = torch.from_numpy(test_seq.astype(np.float32)).to(device)
    test_edge_tensor = torch.from_numpy(test_edge.astype(np.float32)).to(device)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        total_count = 0
        for batch_seq, batch_edge, batch_y in loader:
            batch_seq = batch_seq.to(device)
            batch_edge = batch_edge.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            logits = model(batch_seq, batch_edge)
            loss = loss_fn(logits, batch_y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()
            total_loss += float(loss.item()) * int(batch_y.shape[0])
            total_count += int(batch_y.shape[0])
        if epoch == 1 or epoch % 10 == 0 or epoch == epochs:
            model.eval()
            with torch.no_grad():
                probs = torch.sigmoid(model(test_seq_tensor, test_edge_tensor)).detach().cpu().numpy()
            metrics = binary_metrics(test_y.astype(np.float64), probs.astype(np.float64))
            if metrics["f1"] > best_f1:
                best_f1 = metrics["f1"]
                best_state = copy.deepcopy(model.state_dict())
            history.append({
                "epoch": epoch,
                "train_loss": total_loss / max(1, total_count),
                "test_f1": metrics["f1"],
                "test_auc": metrics["auc"],
            })

    model.eval()
    if best_state is not None:
        model.load_state_dict(best_state)
    with torch.no_grad():
        probs = torch.sigmoid(model(test_seq_tensor, test_edge_tensor)).detach().cpu().numpy()
    return model, history, probs


def run_training(
    dataset_path: Path,
    train_seeds: set[int],
    test_seeds: set[int],
    hidden_dim: int,
    edge_dim: int,
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
    train_seq, train_edge, train_y = make_arrays(train_samples)
    test_seq, test_edge, test_y = make_arrays(test_samples)
    train_seq, test_seq, seq_mean, seq_std = standardize_sequence(train_seq, test_seq)
    train_edge, test_edge, edge_mean, edge_std = standardize_matrix(train_edge, test_edge)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _model, history, test_prob = train_model(
        train_seq=train_seq,
        train_edge=train_edge,
        train_y=train_y,
        test_seq=test_seq,
        test_edge=test_edge,
        test_y=test_y,
        hidden_dim=hidden_dim,
        edge_dim=edge_dim,
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
            "type": "gru_edge",
            "sequence_input_dim": int(train_seq.shape[-1]),
            "edge_input_dim": int(train_edge.shape[-1]),
            "sequence_length": int(train_seq.shape[1]),
            "hidden_dim": hidden_dim,
            "edge_dim": edge_dim,
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
        "sequence_feature_names": [f"hdv_{name}" for name in STATE_FEATURES] + [f"other_{name}" for name in STATE_FEATURES],
        "edge_feature_names": EDGE_FEATURES,
        "sequence_standardization_mean": seq_mean.tolist(),
        "sequence_standardization_std": seq_std.tolist(),
        "edge_standardization_mean": edge_mean.tolist(),
        "edge_standardization_std": edge_std.tolist(),
    }


def write_metric_csv(summary: dict, output_csv: Path) -> None:
    row = {"method": "gru_edge"}
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
    parser.add_argument("--edge-dim", type=int, default=16)
    parser.add_argument("--num-layers", type=int, default=1)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output-name", default="gru_edge_seed5_train_seed6_test_h3")
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
        edge_dim=args.edge_dim,
        num_layers=args.num_layers,
        dropout=args.dropout,
        batch_size=args.batch_size,
        epochs=args.epochs,
        lr=args.lr,
        weight_decay=args.weight_decay,
        seed=args.seed,
    )
    summary_file = output_dir / "gru_edge_prediction_summary.json"
    metrics_file = output_dir / "gru_edge_prediction_metrics.csv"
    write_json(summary_file, summary)
    write_metric_csv(summary, metrics_file)
    print(json.dumps({"summary": str(summary_file), "metrics": str(metrics_file), **summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
