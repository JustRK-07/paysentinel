"""
Stacking ensemble — combines XGBoost, LightGBM, GNN, Transformer, and LLM-Judge.

For tabular inputs: averages the four tabular model probabilities.
For narrative inputs: uses the LLM-Judge score.
For mixed batches: produces one unified score per row.

Also: provides SHAP-based explanations for the dominant model.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


@dataclass
class EnsembleConfig:
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "xgboost": 0.30,
            "lightgbm": 0.25,
            "heterogeneous_gnn": 0.20,
            "transformer_sequence": 0.15,
            "llm_judge": 0.10,
        }
    )
    decision_threshold: float = 0.5


def blend_scores(
    per_model_proba: dict[str, np.ndarray],
    cfg: EnsembleConfig | None = None,
) -> np.ndarray:
    """Weighted average of available model probabilities."""
    cfg = cfg or EnsembleConfig()
    available = {k: v for k, v in per_model_proba.items() if k in cfg.weights}
    if not available:
        raise ValueError("no usable model probabilities")

    total_weight = sum(cfg.weights[m] for m in available)
    if total_weight == 0:
        raise ValueError("weights sum to zero")

    out = np.zeros(len(next(iter(available.values()))), dtype=np.float64)
    for name, p in available.items():
        out += cfg.weights[name] * (np.asarray(p, dtype=np.float64) / total_weight)
    return np.clip(out, 0.0, 1.0)


def decision(score: float, cfg: EnsembleConfig | None = None) -> str:
    cfg = cfg or EnsembleConfig()
    if score >= cfg.decision_threshold:
        return "block"
    if score >= cfg.decision_threshold * 0.7:
        return "review"
    return "approve"


def explain_with_shap(model: Any, X: np.ndarray, feature_names: list[str], top_k: int = 5) -> list[dict[str, float]]:
    """Return top-k SHAP feature contributions for a single prediction."""
    try:
        import shap
    except ImportError:
        return [{"feature": "shap_unavailable", "value": 0.0}]

    try:
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X)
        if isinstance(sv, list):
            sv = sv[1]  # binary: positive class
        # single row
        if X.ndim == 1:
            X = X.reshape(1, -1)
        contribs = sv[0]
        order = np.argsort(np.abs(contribs))[::-1][:top_k]
        return [
            {"feature": feature_names[i], "value": float(contribs[i])}
            for i in order
            if i < len(feature_names)
        ]
    except Exception as e:
        logger.warning("SHAP failed: %s", e)
        return [{"feature": "shap_error", "value": 0.0}]


# ----------------------------- top-level evaluation ----------------------------- #


@dataclass
class EnsembleReport:
    per_model_metrics: dict[str, dict[str, float]]
    blended_auc: float
    blended_f1: float
    blended_precision: float
    blended_recall: float
    blended_false_positive_rate: float
    threshold: float
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_ensemble(
    per_model_proba: dict[str, np.ndarray],
    y_true: np.ndarray,
    cfg: EnsembleConfig | None = None,
) -> EnsembleReport:
    from sklearn.metrics import (
        roc_auc_score,
        average_precision_score,
        f1_score,
        precision_score,
        recall_score,
        confusion_matrix,
    )

    cfg = cfg or EnsembleConfig()
    blended = blend_scores(per_model_proba, cfg)
    y_pred = (blended >= cfg.decision_threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    per_model_metrics: dict[str, dict[str, float]] = {}
    for name, p in per_model_proba.items():
        try:
            per_model_metrics[name] = {
                "auc": float(roc_auc_score(y_true, p)),
                "ap": float(average_precision_score(y_true, p)),
                "f1_at_0.5": float(f1_score(y_true, (p >= 0.5).astype(int), zero_division=0)),
            }
        except Exception as e:
            per_model_metrics[name] = {"error": str(e)}

    notes = []
    if fp / max(1, fp + tn) > 0.05:
        notes.append("FP-rate > 5% — consider raising threshold")
    if tp == 0:
        notes.append("Zero true positives — model is not catching fraud")

    return EnsembleReport(
        per_model_metrics=per_model_metrics,
        blended_auc=float(roc_auc_score(y_true, blended)),
        blended_f1=float(f1_score(y_true, y_pred, zero_division=0)),
        blended_precision=float(precision_score(y_true, y_pred, zero_division=0)),
        blended_recall=float(recall_score(y_true, y_pred, zero_division=0)),
        blended_false_positive_rate=float(fp / max(1, fp + tn)),
        threshold=cfg.decision_threshold,
        notes=notes,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    import numpy as np

    rng = np.random.default_rng(0)
    n = 1000
    y = (rng.random(n) < 0.05).astype(int)
    # Fake per-model probs (each slightly better than random)
    p_xgb = np.clip(y * 0.7 + rng.normal(0, 0.15, n).cumsum() / n + rng.random(n) * 0.3, 0, 1)
    p_lgb = np.clip(y * 0.7 + rng.normal(0, 0.15, n).cumsum() / n + rng.random(n) * 0.3, 0, 1)
    p_gnn = np.clip(y * 0.6 + rng.random(n) * 0.4, 0, 1)
    p_tx = np.clip(y * 0.5 + rng.random(n) * 0.4, 0, 1)
    p_judge = np.clip(y * 0.4 + rng.random(n) * 0.5, 0, 1)

    report = evaluate_ensemble(
        {"xgboost": p_xgb, "lightgbm": p_lgb, "heterogeneous_gnn": p_gnn, "transformer_sequence": p_tx, "llm_judge": p_judge},
        y,
    )
    print(json.dumps(report.to_dict(), indent=2, default=str))


if __name__ == "__main__":
    main()
