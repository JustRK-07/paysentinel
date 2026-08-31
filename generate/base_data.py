"""
Base data loaders — fetch or sample from IEEE-CIS / PaySim.

Both are standard fraud-detection benchmarks. We use them as the statistical
"ground truth" that our synthetic generator must match.

If a local CSV is not present, we synthesise a *realistic* profile dataset
based on published schemas and column distributions so the demo runs offline.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "base"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------- public schemas ----------------------------- #


@dataclass
class DatasetProfile:
    name: str
    n_transactions: int
    fraud_rate: float
    columns: list[str]
    description: str


PAYSIM_PROFILE = DatasetProfile(
    name="paysim",
    n_transactions=6_362_620,
    fraud_rate=0.001_287,
    columns=[
        "step",
        "type",
        "amount",
        "nameOrig",
        "oldbalanceOrg",
        "newbalanceOrig",
        "nameDest",
        "oldbalanceDest",
        "newbalanceDest",
        "isFraud",
        "isFlaggedFraud",
    ],
    description=(
        "PaySim synthetic mobile-money transactions (Lopez-Rojas 2014). "
        "Aggregated from real private datasets. 11 columns, 6 fraud types."
    ),
)

IEEE_CIS_PROFILE = DatasetProfile(
    name="ieee_cis",
    n_transactions=590_540,
    fraud_rate=0.035,
    columns=[
        "TransactionID",
        "isFraud",
        "TransactionDT",
        "TransactionAmt",
        "ProductCD",
        "card1",
        "card2",
        "card3",
        "card4",
        "card5",
        "card6",
        "addr1",
        "addr2",
        "P_emaildomain",
        "R_emaildomain",
        "DeviceInfo",
    ],
    description=(
        "IEEE-CIS Fraud Detection (Vesta, Kaggle 2019). Real e-commerce txns, "
        "394 anonymized features, ~3.5% fraud."
    ),
)


# ----------------------------- synthesis ----------------------------- #


def _seed_from(s: str) -> np.random.Generator:
    h = hashlib.sha256(s.encode()).digest()
    seed = int.from_bytes(h[:8], "big")
    return np.random.default_rng(seed)


def synthesise_paysim_sample(n: int = 50_000) -> pd.DataFrame:
    """Synthesise a PaySim-shaped sample when no local file is available.

    Distributions chosen to match published PaySim statistics (step 1-743,
    5 transaction types, ~0.13% fraud).
    """
    rng = _seed_from("paysim-sample")
    n_fraud = max(1, int(n * PAYSIM_PROFILE.fraud_rate))
    n_legit = n - n_fraud

    types = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
    type_weights = [0.22, 0.22, 0.07, 0.41, 0.08]

    def _sample_legit(n_rows: int) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "step": rng.integers(1, 744, n_rows),
                "type": rng.choice(types, n_rows, p=type_weights),
                "amount": np.round(np.clip(rng.lognormal(8, 1.4, n_rows), 1, 1e6), 2),
                "nameOrig": [f"C{i:09d}" for i in rng.integers(1, 9_999_999, n_rows)],
                "oldbalanceOrg": rng.uniform(0, 5e5, n_rows).round(2),
                "newbalanceOrig": 0.0,
                "nameDest": [f"C{i:09d}" for i in rng.integers(1, 9_999_999, n_rows)],
                "oldbalanceDest": rng.uniform(0, 5e5, n_rows).round(2),
                "newbalanceDest": 0.0,
                "isFraud": 0,
                "isFlaggedFraud": 0,
            }
        )

    def _sample_fraud(n_rows: int) -> pd.DataFrame:
        df = _sample_legit(n_rows)
        df["type"] = rng.choice(["TRANSFER", "CASH_OUT"], n_rows, p=[0.7, 0.3])
        # Fraud amounts skew larger
        df["amount"] = np.round(np.clip(rng.lognormal(10, 1.0, n_rows), 1e3, 1e6), 2)
        # Drains the source account
        df["newbalanceOrig"] = 0.0
        df["newbalanceDest"] = df["oldbalanceDest"] + df["amount"]
        df["isFraud"] = 1
        df["isFlaggedFraud"] = (df["amount"] > 200_000).astype(int)
        return df

    legit = _sample_legit(n_legit)
    fraud = _sample_fraud(n_fraud)
    out = pd.concat([legit, fraud], ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)
    out["newbalanceOrig"] = out["oldbalanceOrg"] - out["amount"]
    out["newbalanceOrig"] = out["newbalanceOrig"].clip(lower=0)
    return out


def synthesise_ieee_cis_sample(n: int = 50_000) -> pd.DataFrame:
    """Synthesise an IEEE-CIS-shaped sample (subset of features)."""
    rng = _seed_from("ieee-cis-sample")
    n_fraud = max(1, int(n * IEEE_CIS_PROFILE.fraud_rate))
    n_legit = n - n_fraud

    def _sample(n_rows: int, fraud: bool) -> pd.DataFrame:
        product_cd = rng.choice(["W", "H", "C", "S", "R"], n_rows, p=[0.45, 0.20, 0.13, 0.12, 0.10])
        card4 = rng.choice(
            ["visa", "mastercard", "american express", "discover"],
            n_rows,
            p=[0.50, 0.34, 0.10, 0.06],
        )
        card6 = rng.choice(["credit", "debit"], n_rows, p=[0.74, 0.26])
        amt = np.clip(rng.lognormal(3.5, 1.0, n_rows), 1, 5_000)
        if fraud:
            amt = np.clip(amt * 1.4 + rng.normal(0, 50, n_rows), 1, 5_000)
        return pd.DataFrame(
            {
                "TransactionID": range(n_rows),
                "isFraud": int(fraud),
                "TransactionDT": rng.integers(86_400, 86_400 * 365, n_rows),
                "TransactionAmt": np.round(amt, 2),
                "ProductCD": product_cd,
                "card1": rng.integers(1_000, 20_000, n_rows),
                "card4": card4,
                "card6": card6,
                "P_emaildomain": rng.choice(
                    ["gmail.com", "yahoo.com", "hotmail.com", "anonymous.com"],
                    n_rows,
                    p=[0.55, 0.25, 0.15, 0.05],
                ),
                "DeviceInfo": rng.choice(
                    ["Windows", "iOS", "MacOS", "Linux", "Android"],
                    n_rows,
                    p=[0.35, 0.25, 0.15, 0.10, 0.15],
                ),
            }
        )

    legit = _sample(n_legit, fraud=False)
    fraud = _sample(n_fraud, fraud=True)
    out = pd.concat([legit, fraud], ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)
    return out


# ----------------------------- loaders ----------------------------- #


def load_or_synthesize(name: str, n: int = 50_000) -> tuple[pd.DataFrame, DatasetProfile]:
    """Load `paysim` or `ieee_cis`. Synthesise if not on disk."""
    profile = PAYSIM_PROFILE if name == "paysim" else IEEE_CIS_PROFILE
    path = DATA_DIR / f"{name}_sample.csv"
    if path.exists():
        logger.info("loading %s from disk", path)
        return pd.read_csv(path), profile
    logger.info("synthesising %s sample (n=%d)", name, n)
    if name == "paysim":
        df = synthesise_paysim_sample(n)
    elif name == "ieee_cis":
        df = synthesise_ieee_cis_sample(n)
    else:
        raise ValueError(f"unknown dataset: {name}")
    df.to_csv(path, index=False)
    return df, profile


# ----------------------------- CLI ----------------------------- #


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    for ds in ("paysim", "ieee_cis"):
        df, profile = load_or_synthesize(ds, n=20_000)
        print(f"{profile.name}: shape={df.shape}, fraud_rate={df['isFraud'].mean():.5f}")


if __name__ == "__main__":
    main()
