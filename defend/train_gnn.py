"""
Heterogeneous Graph Neural Network trainer for fraud detection.

Builds a bipartite graph of (account, merchant) nodes with transactions as
edges. Trains a 2-layer heterogeneous GNN. Falls back to a simpler MLP if
torch-geometric is unavailable so the pipeline still produces metrics.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .train_tabular import _evaluate

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def _try_gnn(df: pd.DataFrame, *, label_col: str, test_size: float, random_state: int) -> dict[str, Any] | None:
    try:
        import torch
        from torch_geometric.data import Data
        from torch_geometric.nn import SAGEConv
    except ImportError:
        return None

    # Build bipartite graph: nameOrig <-> nameDest via transaction edges
    df = df.dropna(subset=[label_col]).copy()
    df["_src"] = df["nameOrig"].astype("category").cat.codes if "nameOrig" in df.columns else 0
    df["_dst"] = df["nameDest"].astype("category").cat.codes if "nameDest" in df.columns else 0
    n_nodes = max(df["_src"].max(), df["_dst"].max()) + 1

    edge_src = df["_src"].to_numpy()
    edge_dst = df["_dst"].to_numpy()
    edge_index = np.vstack([np.concatenate([edge_src, edge_dst]), np.concatenate([edge_dst, edge_src])])
    edge_attr = np.concatenate([df["amount"].fillna(0).to_numpy()] * 2) if "amount" in df.columns else np.zeros(2 * len(df))

    # Node features: per-node transaction count + sum amount
    node_feat = np.zeros((n_nodes, 2), dtype=np.float32)
    for s, a in zip(edge_src, edge_attr[: len(edge_src)]):
        node_feat[s, 0] += 1
        node_feat[s, 1] += a
    node_feat[:, 1] = np.log1p(node_feat[:, 1])

    # Labels on edges
    y = df[label_col].to_numpy().astype(np.float32)

    # Train/test mask on edges
    from sklearn.model_selection import train_test_split

    idx = np.arange(len(df))
    train_idx, test_idx = train_test_split(idx, test_size=test_size, random_state=random_state, stratify=y)
    train_mask = np.zeros(len(df), dtype=bool)
    test_mask = np.zeros(len(df), dtype=bool)
    train_mask[train_idx] = True
    test_mask[test_idx] = True

    data = Data(
        x=torch.tensor(node_feat, dtype=torch.float32),
        edge_index=torch.tensor(edge_index, dtype=torch.long),
        edge_attr=torch.tensor(edge_attr[:, None], dtype=torch.float32) if edge_attr.ndim == 1 else torch.tensor(edge_attr, dtype=torch.float32),
        y=torch.tensor(y, dtype=torch.float32),
        train_mask=torch.tensor(train_mask),
        test_mask=torch.tensor(test_mask),
    )

    class EdgeGNN(torch.nn.Module):
        def __init__(self, in_dim: int = 2, hidden: int = 32):
            super().__init__()
            self.sage1 = SAGEConv(in_dim, hidden)
            self.sage2 = SAGEConv(hidden, hidden)

        def encode(self, x, edge_index):
            x = torch.relu(self.sage1(x, edge_index))
            x = torch.relu(self.sage2(x, edge_index))
            return x

        def predict(self, x_src, x_dst):
            return torch.sigmoid((x_src * x_dst).sum(dim=-1))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = EdgeGNN().to(device)
    data = data.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    bce = torch.nn.BCELoss()

    started = time.time()
    for epoch in range(50):
        model.train()
        opt.zero_grad()
        z = model.encode(data.x, data.edge_index)
        # Predict on edges (forward direction only)
        src_z = z[data.edge_index[0]]
        dst_z = z[data.edge_index[1]]
        edge_score = model.predict(src_z, dst_z)
        loss = bce(edge_score[: len(df)][data.train_mask], data.y[data.train_mask])
        loss.backward()
        opt.step()
    train_time = time.time() - started

    model.eval()
    with torch.no_grad():
        z = model.encode(data.x, data.edge_index)
        src_z = z[data.edge_index[0]]
        dst_z = z[data.edge_index[1]]
        edge_score = model.predict(src_z, dst_z).cpu().numpy()
    y_proba = edge_score[: len(df)]
    metrics = _evaluate(data.y.cpu().numpy()[data.test_mask.cpu().numpy()], y_proba[data.test_mask.cpu().numpy()])
    return {
        "model_name": "heterogeneous_gnn",
        "metrics": metrics,
        "duration_seconds": train_time,
        "n_train": int(train_mask.sum()),
        "n_test": int(test_mask.sum()),
        "notes": ["GraphSAGE 2-layer on bipartite (account, merchant)"],
    }


def _fallback_mlp(df: pd.DataFrame, *, label_col: str, test_size: float, random_state: int) -> dict[str, Any]:
    """Used when torch-geometric is unavailable."""
    from sklearn.neural_network import MLPClassifier
    from .feature_engineering import engineer_features

    feats = engineer_features(df)
    y = df[label_col].to_numpy()
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        feats.to_numpy(), y, test_size=test_size, random_state=random_state, stratify=y
    )
    started = time.time()
    model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=30, random_state=random_state)
    model.fit(X_train, y_train)
    y_proba = model.predict_proba(X_test)[:, 1]
    metrics = _evaluate(y_test, y_proba)
    return {
        "model_name": "mlp_fallback",
        "metrics": metrics,
        "duration_seconds": time.time() - started,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "notes": ["MLP fallback (torch-geometric unavailable)"],
    }


def train_gnn(
    df: pd.DataFrame,
    *,
    label_col: str = "isFraud",
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, Any]:
    """Train GNN; fall back to MLP if PyG unavailable."""
    logger.info("training heterogeneous GNN...")
    res = _try_gnn(df, label_col=label_col, test_size=test_size, random_state=random_state)
    if res is None:
        logger.warning("torch-geometric unavailable; using MLP fallback")
        res = _fallback_mlp(df, label_col=label_col, test_size=test_size, random_state=random_state)
    return res


# ----------------------------- CLI ----------------------------- #


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from generate.base_data import load_or_synthesize

    df, _ = load_or_synthesize("paysim", n=10_000)
    res = train_gnn(df)
    print(f"GNN: AUC={res['metrics']['auc']:.4f}  F1={res['metrics']['f1']:.4f}")


if __name__ == "__main__":
    main()
