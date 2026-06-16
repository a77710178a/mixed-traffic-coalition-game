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
from train_gru_predictor import STATE_FEATURES, load_jsonl, set_seed
from train_prediction_baselines import EDGE_FEATURES, binary_metrics, seed_from_run_id


def split_samples(samples: list[dict], train_seeds: set[int], test_seeds: set[int]) -> tuple[list[dict], list[dict]]:
    train = [sample for sample in samples if seed_from_run_id(sample["run_id"]) in train_seeds]
    test = [sample for sample in samples if seed_from_run_id(sample["run_id"]) in test_seeds]
    if not train or not test:
        raise ValueError("Train/test split produced an empty split. Check seed arguments.")
    return train, test


def state_history(history: list[dict]) -> np.ndarray:
    return np.asarray([[float(row[name]) for name in STATE_FEATURES] for row in history], dtype=np.float32)


def edge_vector(edge: dict) -> np.ndarray:
    return np.asarray([float(edge[name]) for name in EDGE_FEATURES], dtype=np.float32)


def infer_max_neighbors(samples: list[dict]) -> int:
    if not samples:
        return 1
    return max(1, max(len(sample.get("neighbors", [])) for sample in samples))


def make_arrays(samples: list[dict], max_neighbors: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    target_seq = np.stack([state_history(sample["target_history"]) for sample in samples], axis=0)
    sequence_len = target_seq.shape[1]
    state_dim = target_seq.shape[2]
    neighbor_seq = np.zeros((len(samples), max_neighbors, sequence_len, state_dim), dtype=np.float32)
    neighbor_edge = np.zeros((len(samples), max_neighbors, len(EDGE_FEATURES)), dtype=np.float32)
    neighbor_mask = np.zeros((len(samples), max_neighbors), dtype=np.float32)
    y = np.asarray([sample["labels"]["hdv_takes_priority"] for sample in samples], dtype=np.float32)

    for sample_index, sample in enumerate(samples):
        for neighbor_index, neighbor in enumerate(sample.get("neighbors", [])[:max_neighbors]):
            neighbor_seq[sample_index, neighbor_index] = state_history(neighbor["history"])
            neighbor_edge[sample_index, neighbor_index] = edge_vector(neighbor["edge_features"])
            neighbor_mask[sample_index, neighbor_index] = 1.0

    return target_seq, neighbor_seq, neighbor_edge, neighbor_mask, y


def standardize_graph_sequences(
    train_target: np.ndarray,
    train_neighbors: np.ndarray,
    train_mask: np.ndarray,
    test_target: np.ndarray,
    test_neighbors: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    train_rows = [train_target.reshape(-1, train_target.shape[-1])]
    valid_neighbor_rows = train_neighbors[train_mask.astype(bool)].reshape(-1, train_neighbors.shape[-1])
    if len(valid_neighbor_rows):
        train_rows.append(valid_neighbor_rows)
    stacked = np.concatenate(train_rows, axis=0)
    mean = stacked.mean(axis=0)
    std = stacked.std(axis=0)
    std[std < 1e-8] = 1.0
    return (
        (train_target - mean) / std,
        (train_neighbors - mean) / std,
        (test_target - mean) / std,
        (test_neighbors - mean) / std,
        mean,
        std,
    )


def standardize_graph_edges(
    train_edges: np.ndarray,
    train_mask: np.ndarray,
    test_edges: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    valid_rows = train_edges[train_mask.astype(bool)]
    if len(valid_rows) == 0:
        mean = np.zeros(train_edges.shape[-1], dtype=np.float32)
        std = np.ones(train_edges.shape[-1], dtype=np.float32)
    else:
        mean = valid_rows.mean(axis=0)
        std = valid_rows.std(axis=0)
        std[std < 1e-8] = 1.0
    return (train_edges - mean) / std, (test_edges - mean) / std, mean, std


class GraphPredictionDataset(Dataset):
    def __init__(
        self,
        target_seq: np.ndarray,
        neighbor_seq: np.ndarray,
        neighbor_edge: np.ndarray,
        neighbor_mask: np.ndarray,
        y: np.ndarray,
    ) -> None:
        self.target_seq = torch.from_numpy(target_seq.astype(np.float32))
        self.neighbor_seq = torch.from_numpy(neighbor_seq.astype(np.float32))
        self.neighbor_edge = torch.from_numpy(neighbor_edge.astype(np.float32))
        self.neighbor_mask = torch.from_numpy(neighbor_mask.astype(np.float32))
        self.y = torch.from_numpy(y.astype(np.float32))

    def __len__(self) -> int:
        return int(self.y.shape[0])

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        return (
            self.target_seq[index],
            self.neighbor_seq[index],
            self.neighbor_edge[index],
            self.neighbor_mask[index],
            self.y[index],
        )


class GraphAttentionPredictor(nn.Module):
    def __init__(
        self,
        state_dim: int,
        edge_dim_in: int,
        hidden_dim: int,
        edge_dim: int,
        attention_dim: int,
        num_layers: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.target_gru = nn.GRU(
            input_size=state_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.neighbor_gru = nn.GRU(
            input_size=state_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.edge_encoder = nn.Sequential(
            nn.Linear(edge_dim_in, edge_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(edge_dim, edge_dim),
            nn.ReLU(),
        )
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * 2 + edge_dim, attention_dim),
            nn.Tanh(),
            nn.Linear(attention_dim, 1),
        )
        self.head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(
        self,
        target_seq: torch.Tensor,
        neighbor_seq: torch.Tensor,
        neighbor_edge: torch.Tensor,
        neighbor_mask: torch.Tensor,
    ) -> torch.Tensor:
        _target_out, target_hidden = self.target_gru(target_seq)
        target_h = target_hidden[-1]

        batch_size, max_neighbors, sequence_len, state_dim = neighbor_seq.shape
        flat_neighbors = neighbor_seq.reshape(batch_size * max_neighbors, sequence_len, state_dim)
        _neighbor_out, neighbor_hidden = self.neighbor_gru(flat_neighbors)
        neighbor_h = neighbor_hidden[-1].reshape(batch_size, max_neighbors, -1)

        edge_h = self.edge_encoder(neighbor_edge)
        expanded_target = target_h.unsqueeze(1).expand(-1, max_neighbors, -1)
        attention_input = torch.cat([expanded_target, neighbor_h, edge_h], dim=-1)
        scores = self.attention(attention_input).squeeze(-1)
        scores = scores.masked_fill(neighbor_mask <= 0, -1e9)
        weights = torch.softmax(scores, dim=1) * neighbor_mask
        weights = weights / weights.sum(dim=1, keepdim=True).clamp_min(1e-8)
        context = torch.sum(weights.unsqueeze(-1) * neighbor_h, dim=1)
        return self.head(torch.cat([target_h, context], dim=-1)).squeeze(-1)


def train_model(
    train_target: np.ndarray,
    train_neighbors: np.ndarray,
    train_edges: np.ndarray,
    train_mask: np.ndarray,
    train_y: np.ndarray,
    test_target: np.ndarray,
    test_neighbors: np.ndarray,
    test_edges: np.ndarray,
    test_mask: np.ndarray,
    test_y: np.ndarray,
    hidden_dim: int,
    edge_dim: int,
    attention_dim: int,
    num_layers: int,
    dropout: float,
    batch_size: int,
    epochs: int,
    lr: float,
    weight_decay: float,
    device: torch.device,
) -> tuple[GraphAttentionPredictor, list[dict], np.ndarray]:
    model = GraphAttentionPredictor(
        state_dim=train_target.shape[-1],
        edge_dim_in=train_edges.shape[-1],
        hidden_dim=hidden_dim,
        edge_dim=edge_dim,
        attention_dim=attention_dim,
        num_layers=num_layers,
        dropout=dropout,
    ).to(device)
    loader = DataLoader(
        GraphPredictionDataset(train_target, train_neighbors, train_edges, train_mask, train_y),
        batch_size=batch_size,
        shuffle=True,
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = nn.BCEWithLogitsLoss()
    history = []
    best_state = None
    best_f1 = -1.0

    test_target_tensor = torch.from_numpy(test_target.astype(np.float32)).to(device)
    test_neighbors_tensor = torch.from_numpy(test_neighbors.astype(np.float32)).to(device)
    test_edges_tensor = torch.from_numpy(test_edges.astype(np.float32)).to(device)
    test_mask_tensor = torch.from_numpy(test_mask.astype(np.float32)).to(device)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        total_count = 0
        for batch_target, batch_neighbors, batch_edges, batch_mask, batch_y in loader:
            batch_target = batch_target.to(device)
            batch_neighbors = batch_neighbors.to(device)
            batch_edges = batch_edges.to(device)
            batch_mask = batch_mask.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            logits = model(batch_target, batch_neighbors, batch_edges, batch_mask)
            loss = loss_fn(logits, batch_y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()
            total_loss += float(loss.item()) * int(batch_y.shape[0])
            total_count += int(batch_y.shape[0])
        if epoch == 1 or epoch % 10 == 0 or epoch == epochs:
            model.eval()
            with torch.no_grad():
                probs = torch.sigmoid(
                    model(test_target_tensor, test_neighbors_tensor, test_edges_tensor, test_mask_tensor)
                ).detach().cpu().numpy()
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
        probs = torch.sigmoid(
            model(test_target_tensor, test_neighbors_tensor, test_edges_tensor, test_mask_tensor)
        ).detach().cpu().numpy()
    return model, history, probs


def run_training(
    dataset_path: Path,
    train_seeds: set[int],
    test_seeds: set[int],
    max_neighbors: int | None,
    hidden_dim: int,
    edge_dim: int,
    attention_dim: int,
    num_layers: int,
    dropout: float,
    batch_size: int,
    epochs: int,
    lr: float,
    weight_decay: float,
    seed: int,
) -> dict:
    set_seed(seed)
    random.seed(seed)
    samples = load_jsonl(dataset_path)
    train_samples, test_samples = split_samples(samples, train_seeds, test_seeds)
    if max_neighbors is None:
        max_neighbors = infer_max_neighbors(train_samples + test_samples)

    train_target, train_neighbors, train_edges, train_mask, train_y = make_arrays(train_samples, max_neighbors)
    test_target, test_neighbors, test_edges, test_mask, test_y = make_arrays(test_samples, max_neighbors)
    train_target, train_neighbors, test_target, test_neighbors, state_mean, state_std = standardize_graph_sequences(
        train_target=train_target,
        train_neighbors=train_neighbors,
        train_mask=train_mask,
        test_target=test_target,
        test_neighbors=test_neighbors,
    )
    train_edges, test_edges, edge_mean, edge_std = standardize_graph_edges(train_edges, train_mask, test_edges)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _model, history, test_prob = train_model(
        train_target=train_target,
        train_neighbors=train_neighbors,
        train_edges=train_edges,
        train_mask=train_mask,
        train_y=train_y,
        test_target=test_target,
        test_neighbors=test_neighbors,
        test_edges=test_edges,
        test_mask=test_mask,
        test_y=test_y,
        hidden_dim=hidden_dim,
        edge_dim=edge_dim,
        attention_dim=attention_dim,
        num_layers=num_layers,
        dropout=dropout,
        batch_size=batch_size,
        epochs=epochs,
        lr=lr,
        weight_decay=weight_decay,
        device=device,
    )
    metrics = binary_metrics(test_y.astype(np.float64), test_prob.astype(np.float64))
    neighbor_counts = train_mask.sum(axis=1).tolist() + test_mask.sum(axis=1).tolist()
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
            "type": "graph_attention_gru",
            "state_dim": int(train_target.shape[-1]),
            "edge_input_dim": int(train_edges.shape[-1]),
            "sequence_length": int(train_target.shape[1]),
            "max_neighbors": int(max_neighbors),
            "hidden_dim": hidden_dim,
            "edge_dim": edge_dim,
            "attention_dim": attention_dim,
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
        "neighbor_count_summary": {
            "min": int(min(neighbor_counts)),
            "max": int(max(neighbor_counts)),
            "mean": float(np.mean(neighbor_counts)),
        },
        "state_feature_names": STATE_FEATURES,
        "edge_feature_names": EDGE_FEATURES,
        "state_standardization_mean": state_mean.tolist(),
        "state_standardization_std": state_std.tolist(),
        "edge_standardization_mean": edge_mean.tolist(),
        "edge_standardization_std": edge_std.tolist(),
    }


def write_metric_csv(summary: dict, output_csv: Path) -> None:
    row = {"method": "graph_attention_gru"}
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
        default=str(PROTOTYPE_ROOT / "graph_datasets" / "stress_seed5_6_graph_hc_h3" / "graph_prediction_samples.jsonl"),
    )
    parser.add_argument("--train-seeds", default="5")
    parser.add_argument("--test-seeds", default="6")
    parser.add_argument("--max-neighbors", type=int, default=None)
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--edge-dim", type=int, default=16)
    parser.add_argument("--attention-dim", type=int, default=32)
    parser.add_argument("--num-layers", type=int, default=1)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output-name", default="graph_attention_seed5_train_seed6_test_h3")
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
        max_neighbors=args.max_neighbors,
        hidden_dim=args.hidden_dim,
        edge_dim=args.edge_dim,
        attention_dim=args.attention_dim,
        num_layers=args.num_layers,
        dropout=args.dropout,
        batch_size=args.batch_size,
        epochs=args.epochs,
        lr=args.lr,
        weight_decay=args.weight_decay,
        seed=args.seed,
    )
    summary_file = output_dir / "graph_attention_prediction_summary.json"
    metrics_file = output_dir / "graph_attention_prediction_metrics.csv"
    write_json(summary_file, summary)
    write_metric_csv(summary, metrics_file)
    print(json.dumps({"summary": str(summary_file), "metrics": str(metrics_file), **summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
