"""
3-axis fidelity harness for synthetic fraud data.

1. **Statistical fidelity** — column-wise KS test + Wasserstein distance +
   correlation-matrix preservation. Catches "the marginals look right but
   the joint distribution is off."

2. **Behavioral fidelity** — does the generated data preserve *fraud-specific
   patterns* (smurfing shape, mule-graph centrality, fraud amount skew)?
   Addresses the gap noted in
   arXiv 2604.13125 — "Synthetic Tabular Generators Fail to Preserve
   Behavioral Fraud Patterns."

3. **Task-level fidelity** — train a detector on generated data, evaluate on
   held-out real data. If generated data is realistic, the detector should
   transfer.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


# ----------------------------- axis 1: statistical ----------------------------- #


def _numeric_columns(real: pd.DataFrame, synth: pd.DataFrame) -> list[str]:
    return [c for c in real.columns if c in synth.columns and pd.api.types.is_numeric_dtype(real[c])]


def statistical_fidelity(real: pd.DataFrame, synth: pd.DataFrame) -> dict[str, Any]:
    """KS test per numeric column + Wasserstein + correlation preservation."""
    out: dict[str, Any] = {"per_column": {}, "summary": {}}
    cols = _numeric_columns(real, synth)
    if not cols:
        return out

    ks_pass = 0
    wass_avg = 0.0
    for c in cols:
        r = real[c].dropna().to_numpy()
        s = synth[c].dropna().to_numpy()
        if len(r) == 0 or len(s) == 0:
            continue
        ks = stats.ks_2samp(r, s)
        w = stats.wasserstein_distance(r, s) / max(1.0, float(np.std(r)))
        out["per_column"][c] = {"ks_stat": float(ks.statistic), "ks_p": float(ks.pvalue), "wasserstein_norm": float(w)}
        if ks.pvalue > 0.05:
            ks_pass += 1
        wass_avg += w

    # Correlation matrix preservation (numeric only)
    try:
        rc = real[cols].corr().to_numpy()
        sc = synth[cols].corr().to_numpy()
        diff = np.abs(rc - sc)
        corr_mae = float(np.nanmean(diff))
    except Exception:
        corr_mae = float("nan")

    out["summary"] = {
        "n_columns": len(cols),
        "ks_pass_count": ks_pass,
        "ks_pass_rate": ks_pass / max(1, len(cols)),
        "wasserstein_normalised_mean": wass_avg / max(1, len(cols)),
        "correlation_mae": corr_mae,
    }
    return out


# ----------------------------- axis 2: behavioral ----------------------------- #


def behavioral_fidelity(real: pd.DataFrame, synth: pd.DataFrame) -> dict[str, Any]:
    """Fraud-specific behavioral pattern checks."""
    out: dict[str, Any] = {}

    # Fraud amount skew — fraud amounts in PaySim skew 3-5x larger than legit
    if "isFraud" in real.columns and "amount" in real.columns and "isFraud" in synth.columns:
        r_legit_amt = real[real["isFraud"] == 0]["amount"]
        r_fraud_amt = real[real["isFraud"] == 1]["amount"]
        s_legit_amt = synth[synth["isFraud"] == 0]["amount"]
        s_fraud_amt = synth[synth["isFraud"] == 1]["amount"]
        if len(r_fraud_amt) > 5 and len(s_fraud_amt) > 5:
            real_ratio = float(r_fraud_amt.median() / max(1.0, r_legit_amt.median()))
            synth_ratio = float(s_fraud_amt.median() / max(1.0, s_legit_amt.median()))
            out["fraud_amount_ratio_real"] = real_ratio
            out["fraud_amount_ratio_synth"] = synth_ratio
            out["fraud_amount_ratio_drift"] = abs(real_ratio - synth_ratio) / max(1e-6, real_ratio)

    # Micro-split pattern: std-dev of fraud txns from same source
    if {"nameOrig", "isFraud", "amount"}.issubset(real.columns):
        out["smurfing_detection_real"] = _smurfing_score(real)
        out["smurfing_detection_synth"] = _smurfing_score(synth)

    # Mule flow: average fan-out per fraud-origin
    if {"nameOrig", "isFraud"}.issubset(real.columns):
        out["mule_flow_score_real"] = _mule_flow_score(real)
        out["mule_flow_score_synth"] = _mule_flow_score(synth)

    out["summary"] = {
        "n_checks": len([k for k in out if k != "summary"]),
        "max_drift": float(np.nanmax([v for k, v in out.items() if k.endswith("_drift")])) if any(
            k.endswith("_drift") for k in out
        ) else 0.0,
    }
    return out


def _smurfing_score(df: pd.DataFrame) -> float:
    """Higher score = more smurfing behaviour present."""
    fraud = df[df["isFraud"] == 1]
    if len(fraud) < 10:
        return 0.0
    by_src = fraud.groupby("nameOrig")["amount"].agg(["count", "std"]).fillna(0)
    by_src = by_src[by_src["count"] >= 5]
    if len(by_src) == 0:
        return 0.0
    return float((by_src["count"] * (1 / (1 + by_src["std"]))).mean())


def _mule_flow_score(df: pd.DataFrame) -> float:
    """Average fan-out from fraud-origin accounts."""
    fraud = df[df["isFraud"] == 1]
    if len(fraud) == 0:
        return 0.0
    fan_out = fraud.groupby("nameOrig")["nameDest"].nunique()
    return float(fan_out.mean())


# ----------------------------- axis 3: task-level ----------------------------- #


def task_level_fidelity(
    real: pd.DataFrame,
    synth: pd.DataFrame,
    *,
    label_col: str = "isFraud",
    test_size: float = 0.3,
    random_state: int = 42,
) -> dict[str, Any]:
    """Train XGBoost on synthetic data, evaluate on held-out real data.

    High transfer = generated data is realistic enough to be useful.
    """
    try:
        from xgboost import XGBClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import roc_auc_score, average_precision_score, f1_score
    except ImportError:
        return {"error": "xgboost / sklearn not installed"}

    # Build feature matrices (numeric only)
    feat_cols = [c for c in real.columns if c in synth.columns and c != label_col and pd.api.types.is_numeric_dtype(real[c])]
    if not feat_cols or label_col not in real.columns or label_col not in synth.columns:
        return {"error": "insufficient overlapping numeric features"}

    Xr = real[feat_cols].fillna(0).to_numpy()
    yr = real[label_col].to_numpy()
    Xs = synth[feat_cols].fillna(0).to_numpy()
    ys = synth[label_col].to_numpy()

    Xr_train, Xr_test, yr_train, yr_test = train_test_split(
        Xr, yr, test_size=test_size, random_state=random_state, stratify=yr
    )

    # Train on synthetic, evaluate on real (held out)
    model = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05, eval_metric="logloss", random_state=random_state
    )
    model.fit(Xs, ys)

    y_proba = model.predict_proba(Xr_test)[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)

    out = {
        "trained_on": "synthetic",
        "evaluated_on": "real_holdout",
        "n_features": len(feat_cols),
        "auc": float(roc_auc_score(yr_test, y_proba)),
        "ap": float(average_precision_score(yr_test, y_proba)),
        "f1_at_0.5": float(f1_score(yr_test, y_pred, zero_division=0)),
        "synth_size": int(len(Xs)),
        "real_test_size": int(len(Xr_test)),
    }
    return out


# ----------------------------- top-level ----------------------------- #


@dataclass
class FidelityReport:
    statistical: dict[str, Any]
    behavioral: dict[str, Any]
    task_level: dict[str, Any]
    overall_score: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate(real: pd.DataFrame, synth: pd.DataFrame, *, run_task_eval: bool = True) -> FidelityReport:
    """Run the full 3-axis fidelity evaluation."""
    stat = statistical_fidelity(real, synth)
    behav = behavioral_fidelity(real, synth)
    task = task_level_fidelity(real, synth) if run_task_eval else {"skipped": True}

    # Overall score: weighted blend
    ks = stat.get("summary", {}).get("ks_pass_rate", 0.0)
    corr = stat.get("summary", {}).get("correlation_mae", 1.0)
    corr_score = max(0.0, 1.0 - (corr if not np.isnan(corr) else 1.0))
    drift = behav.get("summary", {}).get("max_drift", 0.0)
    behav_score = max(0.0, 1.0 - drift)
    task_auc = task.get("auc", 0.0) if isinstance(task, dict) else 0.0

    overall = 0.30 * ks + 0.20 * corr_score + 0.20 * behav_score + 0.30 * task_auc

    notes: list[str] = []
    if ks < 0.5:
        notes.append("Statistical fidelity low: <50% of columns pass KS test")
    if corr_score < 0.5:
        notes.append("Correlation matrix poorly preserved")
    if behav_score < 0.5:
        notes.append("Behavioral patterns drift >50%")
    if task_auc and task_auc < 0.7:
        notes.append(f"Task transfer AUC = {task_auc:.2f} — synthetic data may be too easy/hard")

    return FidelityReport(
        statistical=stat,
        behavioral=behav,
        task_level=task,
        overall_score=float(overall),
        notes=notes,
    )


# ----------------------------- CLI ----------------------------- #


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from .base_data import load_or_synthesize
    from .txn_generator import generate_attack_batch

    df, profile = load_or_synthesize("paysim", n=10_000)
    batch = generate_attack_batch("PSF-017", "micro_split", df, profile, n_base=500, n_pattern=300)

    real_eval = df.sample(n=2_000, random_state=0)
    report = evaluate(real_eval, batch.df)
    print(f"Overall fidelity: {report.overall_score:.3f}")
    print(f"Notes: {report.notes}")
    import json as _json
    print(_json.dumps(report.to_dict(), indent=2, default=str)[:1200] + "...")


if __name__ == "__main__":
    main()
