"""
Tabular model trainers — XGBoost and LightGBM.

Both models train on the engineered feature matrix and produce probability
scores for each transaction. Used as the workhorse of the ensemble.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .feature_engineering import engineer_features, feature_names

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TrainResult:
    model_name: str
    metrics: dict[str, float]
    feature_importance: dict[str, float]
    duration_seconds: float
    n_train: int
    n_test: int
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _train_test_split(df: pd.DataFrame, label_col: str, *, test_size: float = 0.2, random_state: int = 42):
    from sklearn.model_selection import train_test_split

    feats = engineer_features(df)
    feat_cols = [c for c in feats.columns if c in feature_names() or c.startswith("feature_")]
    X = feats[feat_cols].to_numpy()
    y = df[label_col].to_numpy()
    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y), feat_cols


def _evaluate(y_true: np.ndarray, y_proba: np.ndarray) -> dict[str, float]:
    from sklearn.metrics import (
        roc_auc_score,
        average_precision_score,
        f1_score,
        precision_score,
        recall_score,
        confusion_matrix,
    )

    y_pred = (y_proba >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "auc": float(roc_auc_score(y_true, y_proba)),
        "ap": float(average_precision_score(y_true, y_proba)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "false_positive_rate": float(fp / max(1, fp + tn)),
        "true_positives": int(tp),
        "false_negatives": int(fn),
        "true_negatives": int(tn),
        "false_positives": int(fp),
    }


# ----------------------------- XGBoost ----------------------------- #


def train_xgboost(
    df: pd.DataFrame,
    *,
    label_col: str = "isFraud",
    test_size: float = 0.2,
    random_state: int = 42,
    save: bool = True,
) -> TrainResult:
    try:
        from xgboost import XGBClassifier
    except ImportError:
        raise RuntimeError("xgboost not installed")

    started = time.time()
    (X_train, X_test, y_train, y_test), feat_cols = _train_test_split(
        df, label_col, test_size=test_size, random_state=random_state
    )

    model = XGBClassifier(
        n_estimators=300,
        max_depth=7,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=random_state,
        tree_method="hist",
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    y_proba = model.predict_proba(X_test)[:, 1]
    metrics = _evaluate(y_test, y_proba)

    importance = dict(zip(feat_cols, [float(x) for x in model.feature_importances_]))
    importance = dict(sorted(importance.items(), key=lambda kv: kv[1], reverse=True)[:15])

    if save:
        path = MODELS_DIR / "xgb.json"
        model.save_model(str(path))
        logger.info("saved XGBoost to %s", path)

    return TrainResult(
        model_name="xgboost",
        metrics=metrics,
        feature_importance=importance,
        duration_seconds=time.time() - started,
        n_train=len(X_train),
        n_test=len(X_test),
    )


# ----------------------------- LightGBM ----------------------------- #


def train_lightgbm(
    df: pd.DataFrame,
    *,
    label_col: str = "isFraud",
    test_size: float = 0.2,
    random_state: int = 42,
    save: bool = True,
) -> TrainResult:
    try:
        import lightgbm as lgb
    except ImportError:
        raise RuntimeError("lightgbm not installed")

    started = time.time()
    (X_train, X_test, y_train, y_test), feat_cols = _train_test_split(
        df, label_col, test_size=test_size, random_state=random_state
    )

    model = lgb.LGBMClassifier(
        n_estimators=300,
        max_depth=7,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=random_state,
        verbose=-1,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], callbacks=[lgb.early_stopping(20, verbose=False)])
    y_proba = model.predict_proba(X_test)[:, 1]
    metrics = _evaluate(y_test, y_proba)

    importance = dict(zip(feat_cols, [float(x) for x in model.feature_importances_]))
    importance = dict(sorted(importance.items(), key=lambda kv: kv[1], reverse=True)[:15])

    if save:
        path = MODELS_DIR / "lgb.txt"
        model.booster_.save_model(str(path))
        logger.info("saved LightGBM to %s", path)

    return TrainResult(
        model_name="lightgbm",
        metrics=metrics,
        feature_importance=importance,
        duration_seconds=time.time() - started,
        n_train=len(X_train),
        n_test=len(X_test),
    )


# ----------------------------- CLI ----------------------------- #


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from generate.base_data import load_or_synthesize

    df, _ = load_or_synthesize("paysim", n=20_000)
    print("--- XGBoost ---")
    res = train_xgboost(df)
    print(f"AUC={res.metrics['auc']:.4f}  F1={res.metrics['f1']:.4f}  FP-rate={res.metrics['false_positive_rate']:.4f}")
    print("--- LightGBM ---")
    res = train_lightgbm(df)
    print(f"AUC={res.metrics['auc']:.4f}  F1={res.metrics['f1']:.4f}  FP-rate={res.metrics['false_positive_rate']:.4f}")


if __name__ == "__main__":
    main()
