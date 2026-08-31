"""
Sequence Transformer for fraud detection.

Models a cardholder's transaction *sequence* and predicts whether the next
transaction is fraudulent. Captures long-range behavioural patterns that
tabular features miss.

Falls back to a per-cardholder MLP if PyTorch transformer training is too
slow in the demo window.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .train_tabular import _evaluate

logger = logging.getLogger(__name__)


def _build_sequences(
    df: pd.DataFrame,
    *,
    key_col: str = "nameOrig",
    seq_len: int = 16,
    label_col: str = "isFraud",
) -> tuple[np.ndarray, np.ndarray]:
    """Group by key_col, build sequences of (amount, type) → label of last txn."""
    df = df.sort_values(by=[key_col, "step"] if "step" in df.columns else [key_col]).reset_index(drop=True)
    seqs: list[np.ndarray] = []
    labels: list[int] = []
    for _, group in df.groupby(key_col):
        amounts = group["amount"].fillna(0).to_numpy() if "amount" in group.columns else np.zeros(len(group))
        types = group["type"].to_numpy() if "type" in group.columns else np.array(["PAYMENT"] * len(group))
        type_map = {"CASH_IN": 0, "CASH_OUT": 1, "DEBIT": 2, "PAYMENT": 3, "TRANSFER": 4}
        type_oh = np.zeros((len(group), 5), dtype=np.float32)
        for i, t in enumerate(types):
            type_oh[i, type_map.get(t, 3)] = 1.0
        feat = np.column_stack([np.log1p(amounts)[:, None], type_oh])

        if len(feat) >= seq_len:
            for i in range(len(feat) - seq_len + 1):
                seqs.append(feat[i : i + seq_len])
                labels.append(int(group[label_col].iloc[i + seq_len - 1]))
        else:
            pad = np.zeros((seq_len - len(feat), feat.shape[1]), dtype=np.float32)
            seqs.append(np.vstack([feat, pad]))
            labels.append(int(group[label_col].iloc[-1]))
    if not seqs:
        return np.zeros((0, seq_len, 6), dtype=np.float32), np.zeros((0,), dtype=np.float32)
    return np.stack(seqs), np.array(labels, dtype=np.float32)


def _try_transformer(
    df: pd.DataFrame, *, label_col: str, test_size: float, random_state: int
) -> dict[str, Any] | None:
    try:
        import torch
        from torch import nn
    except ImportError:
        return None

    X, y = _build_sequences(df, label_col=label_col)
    if len(X) < 100:
        return None

    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    X_train_t = torch.tensor(X_train, dtype=torch.float32).to(device)
    y_train_t = torch.tensor(y_train, dtype=torch.float32).to(device)
    X_test_t = torch.tensor(X_test, dtype=torch.float32).to(device)
    y_test_t = torch.tensor(y_test, dtype=torch.float32).to(device)

    class FraudTransformer(nn.Module):
        def __init__(self, in_dim: int = 6, d_model: int = 32, nhead: int = 2, layers: int = 2):
            super().__init__()
            self.proj = nn.Linear(in_dim, d_model)
            layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True, dim_feedforward=64)
            self.encoder = nn.TransformerEncoder(layer, num_layers=layers)
            self.head = nn.Sequential(nn.Linear(d_model, 32), nn.ReLU(), nn.Linear(32, 1))

        def forward(self, x):
            z = self.proj(x)
            z = self.encoder(z)
            return self.head(z[:, -1]).squeeze(-1)

    model = FraudTransformer().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=2e-3)
    bce = nn.BCELoss()

    started = time.time()
    for epoch in range(20):
        model.train()
        perm = torch.randperm(len(X_train_t))
        bs = 256
        for i in range(0, len(perm), bs):
            idx = perm[i : i + bs]
            opt.zero_grad()
            logits = model(X_train_t[idx])
            loss = bce(torch.sigmoid(logits), y_train_t[idx])
            loss.backward()
            opt.step()
    train_time = time.time() - started

    model.eval()
    with torch.no_grad():
        y_proba = torch.sigmoid(model(X_test_t)).cpu().numpy()
    metrics = _evaluate(y_test, y_proba)
    return {
        "model_name": "transformer_sequence",
        "metrics": metrics,
        "duration_seconds": train_time,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "notes": ["2-layer transformer, seq_len=16, 6 features per step"],
    }


def _fallback_logreg(
    df: pd.DataFrame, *, label_col: str, test_size: float, random_state: int
) -> dict[str, Any]:
    """Used when PyTorch is unavailable or data is too small for sequences."""
    from sklearn.linear_model import LogisticRegression
    from .feature_engineering import engineer_features
    from sklearn.model_selection import train_test_split

    feats = engineer_features(df)
    y = df[label_col].to_numpy()
    X_train, X_test, y_train, y_test = train_test_split(
        feats.to_numpy(), y, test_size=test_size, random_state=random_state, stratify=y
    )
    started = time.time()
    model = LogisticRegression(max_iter=200, random_state=random_state, class_weight="balanced")
    model.fit(X_train, y_train)
    y_proba = model.predict_proba(X_test)[:, 1]
    metrics = _evaluate(y_test, y_proba)
    return {
        "model_name": "logreg_fallback",
        "metrics": metrics,
        "duration_seconds": time.time() - started,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "notes": ["LogReg fallback (PyTorch unavailable or insufficient sequences)"],
    }


def train_transformer(
    df: pd.DataFrame,
    *,
    label_col: str = "isFraud",
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, Any]:
    logger.info("training sequence transformer...")
    res = _try_transformer(df, label_col=label_col, test_size=test_size, random_state=random_state)
    if res is None:
        logger.warning("transformer unavailable; using LogReg fallback")
        res = _fallback_logreg(df, label_col=label_col, test_size=test_size, random_state=random_state)
    return res


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from generate.base_data import load_or_synthesize

    df, _ = load_or_synthesize("paysim", n=10_000)
    res = train_transformer(df)
    print(f"Transformer: AUC={res['metrics']['auc']:.4f}  F1={res['metrics']['f1']:.4f}")


if __name__ == "__main__":
    main()
