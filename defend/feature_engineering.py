"""
Feature engineering — 25+ behavioral + transactional features per transaction.

Works on both PaySim-style and IEEE-CIS-style data; missing columns are
filled with safe defaults.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the full feature matrix. Always returns numeric, NaN-safe."""
    df = df.copy()

    # ---- raw / log / ratio ----
    if "amount" in df.columns:
        df["feature_amount"] = df["amount"].fillna(0).astype(float)
        df["feature_amount_log"] = np.log1p(df["feature_amount"])
        if "oldbalanceOrg" in df.columns:
            df["feature_amount_to_balance_ratio"] = df["feature_amount"] / np.maximum(
                1.0, df["oldbalanceOrg"].fillna(0)
            )
    else:
        df["feature_amount"] = 0.0
        df["feature_amount_log"] = 0.0

    if "step" in df.columns:
        df["feature_step_hour"] = (df["step"].fillna(0).astype(int) % 24)
    else:
        df["feature_step_hour"] = 0

    if {"oldbalanceOrg", "newbalanceOrig"}.issubset(df.columns):
        df["feature_balance_orig_delta"] = (
            df["oldbalanceOrg"].fillna(0) - df["newbalanceOrig"].fillna(0)
        )
    else:
        df["feature_balance_orig_delta"] = 0.0

    if {"oldbalanceDest", "newbalanceDest"}.issubset(df.columns):
        df["feature_balance_dest_delta"] = (
            df["newbalanceDest"].fillna(0) - df["oldbalanceDest"].fillna(0)
        )
    else:
        df["feature_balance_dest_delta"] = 0.0

    # ---- categorical: type (one-hot a small subset) ----
    if "type" in df.columns:
        for t in ["TRANSFER", "CASH_OUT", "PAYMENT", "CASH_IN", "DEBIT"]:
            df[f"feature_type_{t.lower()}"] = (df["type"] == t).astype(int)
    else:
        for t in ["transfer", "cash_out", "payment", "cash_in", "debit"]:
            df[f"feature_type_{t}"] = 0

    # ---- velocity / behavioral ----
    sort_cols = [c for c in ["nameOrig", "step"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(by=sort_cols).reset_index(drop=True)
    if {"nameOrig", "step"}.issubset(df.columns):
        df["feature_src_count_1h"] = (
            df.groupby("nameOrig")["step"].transform(lambda s: s.diff().lt(2).cumsum()).fillna(0)
        )
        df["feature_src_count_24h"] = (
            df.groupby("nameOrig")["step"].transform(lambda s: s.diff().lt(25).cumsum()).fillna(0)
        )
    else:
        df["feature_src_count_1h"] = 0
        df["feature_src_count_24h"] = 0

    # Sum and rolling features — wrap in try so small/edge data doesn't crash
    if "nameOrig" in df.columns:
        try:
            df["feature_src_sum_1h"] = (
                df.groupby("nameOrig")["feature_amount"]
                .transform(lambda s: s.rolling(min(20, len(s)), min_periods=1).sum())
            )
        except Exception:
            df["feature_src_sum_1h"] = 0.0
        try:
            df["feature_dest_count_24h"] = (
                df.groupby("nameDest")["step"].transform(lambda s: s.diff().lt(25).cumsum()).fillna(0)
                if "nameDest" in df.columns and "step" in df.columns else 0
            )
            df["feature_src_unique_dest_24h"] = (
                df.groupby("nameOrig")["nameDest"].transform(lambda s: s.rolling(min(50, len(s)), min_periods=1).nunique())
                if "nameDest" in df.columns else 0
            )
        except Exception:
            df["feature_dest_count_24h"] = 0
            df["feature_src_unique_dest_24h"] = 0
    else:
        df["feature_src_sum_1h"] = 0.0
        df["feature_dest_count_24h"] = 0
        df["feature_src_unique_dest_24h"] = 0

    if {"nameOrig", "nameDest"}.issubset(df.columns):
        df["feature_is_first_seen_dest"] = (
            ~df.duplicated(subset=["nameOrig", "nameDest"]).astype(int)
        )
    else:
        df["feature_is_first_seen_dest"] = 0

    # ---- amount distribution ----
    if {"nameOrig", "feature_amount"}.issubset(df.columns):
        user_stats = df.groupby("nameOrig")["feature_amount"].agg(["mean", "std"]).fillna(0)
        df = df.merge(user_stats.rename(columns={"mean": "_user_mean", "std": "_user_std"}), on="nameOrig", how="left")
        df["_user_std"] = df["_user_std"].replace(0, 1).fillna(1)
        df["feature_amount_zscore_user"] = (df["feature_amount"] - df["_user_mean"]) / df["_user_std"]
        df["feature_amount_percentile_user"] = df.groupby("nameOrig")["feature_amount"].rank(pct=True)
        df = df.drop(columns=["_user_mean", "_user_std"])
    else:
        df["feature_amount_zscore_user"] = 0.0
        df["feature_amount_percentile_user"] = 0.5

    # ---- pattern flags ----
    df["feature_small_amount_flag"] = (df["feature_amount"] < 10_000).astype(int)
    if "newbalanceOrig" in df.columns:
        df["feature_drain_flag"] = (
            (df["newbalanceOrig"].fillna(-1) == 0) & (df["feature_amount"] > 0)
        ).astype(int)
    else:
        df["feature_drain_flag"] = 0
    df["feature_transfer_only_flag"] = (
        (df.get("feature_type_transfer", 0) == 1) & (df.get("oldbalanceOrg", 0) > 200_000)
    ).astype(int)

    # ---- merchant / device frequency (IEEE-CIS shape) ----
    if "DeviceInfo" in df.columns:
        device_freq = df["DeviceInfo"].value_counts(normalize=True)
        df["feature_device_freq"] = np.log1p(df["DeviceInfo"].map(device_freq).fillna(0.001))
    else:
        df["feature_device_freq"] = 0.0

    if "P_emaildomain" in df.columns:
        email_freq = df["P_emaildomain"].value_counts(normalize=True)
        df["feature_email_domain_freq"] = np.log1p(df["P_emaildomain"].map(email_freq).fillna(0.001))
    else:
        df["feature_email_domain_freq"] = 0.0

    # ---- select feature columns ----
    feature_cols = [c for c in df.columns if c.startswith("feature_")]
    return df[feature_cols].fillna(0)


def feature_names() -> list[str]:
    """Return the canonical list of engineered feature names (order-stable)."""
    base = [
        "feature_amount",
        "feature_amount_log",
        "feature_amount_to_balance_ratio",
        "feature_step_hour",
        "feature_balance_orig_delta",
        "feature_balance_dest_delta",
        "feature_type_transfer",
        "feature_type_cash_out",
        "feature_type_payment",
        "feature_type_cash_in",
        "feature_type_debit",
        "feature_src_count_1h",
        "feature_src_sum_1h",
        "feature_src_count_24h",
        "feature_dest_count_24h",
        "feature_src_unique_dest_24h",
        "feature_is_first_seen_dest",
        "feature_amount_zscore_user",
        "feature_amount_percentile_user",
        "feature_small_amount_flag",
        "feature_drain_flag",
        "feature_transfer_only_flag",
        "feature_device_freq",
        "feature_email_domain_freq",
    ]
    return base


# ----------------------------- CLI ----------------------------- #


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from generate.base_data import load_or_synthesize

    df, _ = load_or_synthesize("paysim", n=5_000)
    feats = engineer_features(df)
    print(f"feature matrix: shape={feats.shape}, columns={len(feature_names())}")
    print(f"first row: {feats.iloc[0].to_dict()}")


if __name__ == "__main__":
    main()
