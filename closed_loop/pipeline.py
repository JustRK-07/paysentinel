"""Closed-loop pipeline — Generate → Defend → failure-seeded re-Generate."""

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

LOOP_DIR = Path(__file__).parent.parent / "results" / "loop"
LOOP_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class IterationResult:
    iteration: int
    n_train: int
    n_test: int
    per_model_metrics: dict[str, dict[str, float]]
    blended_metrics: dict[str, float]
    failure_summary: dict[str, Any]
    new_attack_seeds: list[str]
    duration_seconds: float
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LoopSummary:
    n_iterations: int
    iterations: list[IterationResult]
    auc_progression: list[float]
    f1_progression: list[float]
    final_blended_auc: float
    final_blended_f1: float
    total_duration_seconds: float
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _analyse_failures(
    df_test: pd.DataFrame,
    y_proba: np.ndarray,
    *,
    top_k: int = 20,
) -> dict[str, Any]:
    """Look at the top-K most-missed fraud cases — these become attack seeds."""
    fraud_mask = df_test["isFraud"].to_numpy() == 1
    fraud_idx = np.where(fraud_mask)[0]
    if len(fraud_idx) == 0:
        return {"n_fraud_in_test": 0}

    fraud_proba = y_proba[fraud_idx]
    missed = fraud_idx[np.argsort(fraud_proba)[:top_k]]
    missed_df = df_test.iloc[missed]

    summary: dict[str, Any] = {
        "n_fraud_in_test": int(fraud_mask.sum()),
        "n_missed_top_k": int(len(missed)),
        "missed_amount_stats": {
            "mean": float(missed_df["amount"].mean()) if "amount" in missed_df.columns else None,
            "median": float(missed_df["amount"].median()) if "amount" in missed_df.columns else None,
        },
        "missed_type_distribution": (
            missed_df["type"].value_counts().to_dict() if "type" in missed_df.columns else {}
        ),
    }
    return summary


def _seed_new_attacks(failure_summary: dict[str, Any], iteration: int) -> list[str]:
    """Generate new attack-vector IDs based on failure patterns."""
    seeds: list[str] = []
    type_dist = failure_summary.get("missed_type_distribution", {})
    if type_dist.get("TRANSFER", 0) > 0:
        seeds.append(f"PSF-CL{iteration:02d}-A:TRANSFER-missed (micro-split refinement)")
    if type_dist.get("CASH_OUT", 0) > 0:
        seeds.append(f"PSF-CL{iteration:02d}-B:CASH_OUT-missed (refund fraud refinement)")
    if failure_summary.get("missed_amount_stats", {}).get("median"):
        median = failure_summary["missed_amount_stats"]["median"]
        if median > 100_000:
            seeds.append(f"PSF-CL{iteration:02d}-C:high-amount-transfer-evasion")
        elif median < 1_000:
            seeds.append(f"PSF-CL{iteration:02d}-D:low-amount-card-testing-variant")
    if not seeds:
        seeds.append(f"PSF-CL{iteration:02d}-Z:composite-failure-pattern")
    return seeds


def run_loop(
    *,
    base_dataset: str = "paysim",
    base_n: int = 20_000,
    iterations: int = 3,
    n_per_attack: int = 800,
    seed: int = 42,
) -> LoopSummary:
    """Run the closed-loop pipeline for N iterations."""
    from generate.base_data import load_or_synthesize
    from generate.pipeline import run_pipeline
    from defend.train import train_all

    started = time.time()
    iter_results: list[IterationResult] = []

    for i in range(iterations):
        iter_started = time.time()
        logger.info("=== ITERATION %d/%d ===", i + 1, iterations)

        # Generate
        gen_summary = run_pipeline(
            base_dataset=base_dataset,
            base_n=base_n,
            n_per_txn_attack=n_per_attack,
            run_fidelity=(i == 0),  # only first iter (saves time)
        )
        synth_path = Path(__file__).parent.parent / "data" / "synthetic" / "transactions.parquet"
        synth_df = pd.read_parquet(synth_path) if synth_path.exists() else None

        # Use combined: 70% synthetic + 30% real for training
        base_df, _ = load_or_synthesize(base_dataset, n=base_n)
        if synth_df is not None and not synth_df.empty:
            train_df = pd.concat([base_df.sample(frac=0.5, random_state=seed), synth_df], ignore_index=True)
        else:
            train_df = base_df

        # Defend
        defend_summary = train_all(train_df)
        per_model = defend_summary.get("per_model", {})
        ensemble_metrics = (defend_summary.get("ensemble") or {}).get("per_model_metrics", {})

        # Find failures by replaying XGBoost on a real-data test slice
        from sklearn.model_selection import train_test_split
        from defend.feature_engineering import engineer_features
        import xgboost as xgb

        feats = engineer_features(base_df)
        y = base_df["isFraud"].to_numpy()
        _, X_test, _, y_test = train_test_split(
            feats.to_numpy(), y, test_size=0.2, random_state=seed, stratify=y
        )
        X_test_df = base_df.iloc[len(X_test) * 4 :].copy()  # approximation; small set
        try:
            m = xgb.XGBClassifier()
            m.load_model(str(Path(__file__).parent.parent / "data" / "models" / "xgb.json"))
            y_proba = m.predict_proba(X_test)[:, 1]
            failure_summary = _analyse_failures(
                base_df.sample(n=len(X_test), random_state=seed).reset_index(drop=True),
                y_proba,
            )
            new_seeds = _seed_new_attacks(failure_summary, i + 1)
        except Exception as e:
            logger.warning("failure analysis skipped: %s", e)
            failure_summary = {"error": str(e)}
            new_seeds = []

        notes: list[str] = []
        blended = defend_summary.get("ensemble") or {}
        if blended.get("blended_auc", 0) < 0.7:
            notes.append("Blended AUC below 0.7 — consider more training data or features")

        result = IterationResult(
            iteration=i + 1,
            n_train=int(len(train_df)),
            n_test=int(len(X_test)),
            per_model_metrics={k: v.get("metrics", {}) for k, v in per_model.items()},
            blended_metrics={
                k: v for k, v in (blended.items() if blended else []) if isinstance(v, (int, float))
            },
            failure_summary=failure_summary,
            new_attack_seeds=new_seeds,
            duration_seconds=time.time() - iter_started,
            notes=notes,
        )
        iter_results.append(result)
        (LOOP_DIR / f"iteration_{i+1:02d}.json").write_text(
            json.dumps(result.to_dict(), indent=2, default=str), encoding="utf-8"
        )

    final_auc = iter_results[-1].blended_metrics.get("blended_auc", 0.0) if iter_results else 0.0
    final_f1 = iter_results[-1].blended_metrics.get("blended_f1", 0.0) if iter_results else 0.0

    summary = LoopSummary(
        n_iterations=iterations,
        iterations=iter_results,
        auc_progression=[r.blended_metrics.get("blended_auc", 0.0) for r in iter_results],
        f1_progression=[r.blended_metrics.get("blended_f1", 0.0) for r in iter_results],
        final_blended_auc=final_auc,
        final_blended_f1=final_f1,
        total_duration_seconds=time.time() - started,
        notes=[],
    )
    (LOOP_DIR / "summary.json").write_text(json.dumps(summary.to_dict(), indent=2, default=str), encoding="utf-8")
    logger.info("loop done — final AUC=%.4f F1=%.4f", final_auc, final_f1)
    return summary


def main() -> None:
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--base", default="paysim")
    parser.add_argument("--base-n", type=int, default=20_000)
    args = parser.parse_args()
    summary = run_loop(iterations=args.iterations, base_dataset=args.base, base_n=args.base_n)
    print(json.dumps(summary.to_dict(), indent=2, default=str)[:2000] + "...")


if __name__ == "__main__":
    main()
