"""
Top-level training orchestrator — runs all four detection models and
produces a unified summary.

Usage:
    python -m defend.train
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .ensemble import EnsembleConfig, evaluate_ensemble
from .train_gnn import train_gnn
from .train_tabular import train_lightgbm, train_xgboost
from .train_transformer import train_transformer

logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def train_all(
    df: pd.DataFrame,
    *,
    label_col: str = "isFraud",
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, Any]:
    """Train all four detection models. Return summary with metrics + ensembles."""
    started = time.time()

    logger.info("training XGBoost...")
    xgb_res = train_xgboost(df, label_col=label_col, test_size=test_size, random_state=random_state)

    logger.info("training LightGBM...")
    lgb_res = train_lightgbm(df, label_col=label_col, test_size=test_size, random_state=random_state)

    logger.info("training heterogeneous GNN...")
    gnn_res = train_gnn(df, label_col=label_col, test_size=test_size, random_state=random_state)

    logger.info("training sequence transformer...")
    tx_res = train_transformer(df, label_col=label_col, test_size=test_size, random_state=random_state)

    # Re-extract test-set probabilities for ensemble evaluation
    from sklearn.model_selection import train_test_split
    from .feature_engineering import engineer_features

    feats = engineer_features(df)
    y = df[label_col].to_numpy()
    _, X_test, _, y_test = train_test_split(
        feats.to_numpy(), y, test_size=test_size, random_state=random_state, stratify=y
    )

    per_model_proba: dict[str, np.ndarray] = {}
    try:
        import xgboost as xgb

        m = xgb.XGBClassifier()
        m.load_model(str(Path(__file__).parent.parent / "data" / "models" / "xgb.json"))
        per_model_proba["xgboost"] = m.predict_proba(X_test)[:, 1]
    except Exception as e:
        logger.warning("xgb predict skipped: %s", e)

    try:
        import lightgbm as lgb

        m = lgb.LGBMClassifier()
        m.booster_ = lgb.Booster(model_file=str(Path(__file__).parent.parent / "data" / "models" / "lgb.txt"))
        per_model_proba["lightgbm"] = m.predict_proba(X_test)[:, 1]
    except Exception as e:
        logger.warning("lgb predict skipped: %s", e)

    # For GNN / transformer we don't have easily-replayable probs here;
    # the per_model_metrics in their results will reflect standalone performance.
    ensemble_report = None
    if len(per_model_proba) >= 1:
        # Add synthetic judge-like probs from GNN/Transformer metrics
        # (since they need separate eval sets) — we just record them in summary
        try:
            ensemble_report = evaluate_ensemble(per_model_proba, y_test)
        except Exception as e:
            logger.warning("ensemble eval failed: %s", e)

    summary = {
        "duration_seconds": time.time() - started,
        "per_model": {
            "xgboost": xgb_res.to_dict(),
            "lightgbm": lgb_res.to_dict(),
            "heterogeneous_gnn": gnn_res,
            "transformer_sequence": tx_res,
        },
        "ensemble": ensemble_report.to_dict() if ensemble_report else None,
    }
    out = RESULTS_DIR / "defend_summary.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    logger.info("wrote %s", out)
    return summary


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from generate.base_data import load_or_synthesize

    df, _ = load_or_synthesize("paysim", n=20_000)
    summary = train_all(df)

    print("\n=== Per-model metrics ===")
    for name, res in summary["per_model"].items():
        m = res.get("metrics", {})
        if "auc" in m:
            print(f"  {name:24s}  AUC={m['auc']:.4f}  F1={m['f1']:.4f}  FP-rate={m['false_positive_rate']:.4f}")
        else:
            print(f"  {name:24s}  (no metrics)")

    if summary["ensemble"]:
        e = summary["ensemble"]
        print(
            f"\n=== Ensemble ===\n  blended AUC={e['blended_auc']:.4f}  "
            f"F1={e['blended_f1']:.4f}  FP-rate={e['blended_false_positive_rate']:.4f}"
        )


if __name__ == "__main__":
    main()
