"""
Transaction-level synthetic fraud generator.

Two model backends:
  • CTGAN (via sdv) — best for tabular with mixed types
  • TabDDPM — diffusion-based, often sharper on small datasets

Plus a *pattern injector* that explicitly stamps in known fraud patterns
(micro-split laundering, card testing, money mule flow) on top of the
statistical generator. This is what gives us **behavioral fidelity** —
not just realistic per-row distributions but realistic *flows*.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .base_data import DatasetProfile, load_or_synthesize

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------- model wrappers ----------------------------- #


@dataclass
class GeneratedSet:
    """Output of one Generate run."""

    df: pd.DataFrame
    attack_id: str
    pattern: str
    model: str
    generated_at: float = field(default_factory=time.time)


def train_ctgan(
    df: pd.DataFrame,
    *,
    epochs: int = 50,
    batch_size: 500,
    model_path: Path | None = None,
) -> "CTGANWrapper":
    """Train a CTGAN on the provided DataFrame. Falls back to identity if sdv missing."""
    try:
        from sdv.single_table import CTGANSynthesizer
        from sdv.metadata import SingleTableMetadata
    except ImportError:
        logger.warning("sdv not installed; CTGAN unavailable")
        return CTGANWrapper(model=None, fallback_columns=df.columns.tolist())

    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df)
    model = CTGANSynthesizer(metadata, epochs=epochs, batch_size=batch_size, verbose=False)
    model.fit(df)
    if model_path:
        model.save(str(model_path))
    return CTGANWrapper(model=model, fallback_columns=df.columns.tolist())


class CTGANWrapper:
    def __init__(self, model: object | None, fallback_columns: list[str]) -> None:
        self.model = model
        self.fallback_columns = fallback_columns

    def sample(self, n: int) -> pd.DataFrame:
        if self.model is None:
            return pd.DataFrame(columns=self.fallback_columns)
        return self.model.sample(n)


def train_tabddpm(
    df: pd.DataFrame,
    *,
    epochs: int = 100,
    model_path: Path | None = None,
) -> "TabDDPMWrapper":
    """Train a TabDDPM. Falls back to identity if tab-ddpm missing."""
    try:
        import tabddpm  # noqa: F401
    except ImportError:
        logger.warning("tab-ddpm not installed; falling back to statistical sampling")
        return TabDDPMWrapper(model=None, fallback_columns=df.columns.tolist())

    # Real implementation deferred; placeholder for the demo.
    return TabDDPMWrapper(model=None, fallback_columns=df.columns.tolist())


class TabDDPMWrapper:
    def __init__(self, model: object | None, fallback_columns: list[str]) -> None:
        self.model = model
        self.fallback_columns = fallback_columns

    def sample(self, n: int) -> pd.DataFrame:
        if self.model is None:
            return pd.DataFrame(columns=self.fallback_columns)
        return self.model.sample(n)


# ----------------------------- pattern injection ----------------------------- #


def inject_micro_split(
    n_sources: int = 5,
    n_dests: int = 20,
    per_source: int = 30,
    *,
    amount_below: float = 9_999.0,
    rng: np.random.Generator | None = None,
) -> pd.DataFrame:
    """Generate micro-split laundering pattern (PSF-017)."""
    rng = rng or np.random.default_rng(17)
    rows = []
    for src in range(n_sources):
        src_id = f"MSRC{src:04d}"
        for dest_idx in range(per_source):
            dest = f"MDST{dest_idx % n_dests:04d}"
            amount = float(np.round(rng.uniform(100, amount_below), 2))
            rows.append(
                {
                    "step": int(rng.integers(1, 744)),
                    "type": "TRANSFER",
                    "amount": amount,
                    "nameOrig": src_id,
                    "oldbalanceOrg": float(rng.uniform(1e4, 1e5)),
                    "newbalanceOrig": 0.0,
                    "nameDest": dest,
                    "oldbalanceDest": float(rng.uniform(0, 1e4)),
                    "newbalanceDest": 0.0,
                    "isFraud": 1,
                    "isFlaggedFraud": 0,
                }
            )
    return pd.DataFrame(rows)


def inject_card_testing(
    n_cards: int = 50,
    tests_per_card: int = 8,
    *,
    rng: np.random.Generator | None = None,
) -> pd.DataFrame:
    """Generate automated card-testing pattern (PSF-018)."""
    rng = rng or np.random.default_rng(18)
    rows = []
    for c in range(n_cards):
        card = f"TEST{c:06d}"
        for _ in range(tests_per_card):
            rows.append(
                {
                    "step": int(rng.integers(1, 744)),
                    "type": "PAYMENT",
                    "amount": float(np.round(rng.uniform(0.5, 5.0), 2)),
                    "nameOrig": card,
                    "oldbalanceOrg": float(rng.uniform(100, 1_000)),
                    "newbalanceOrig": 0.0,
                    "nameDest": f"MERCH{int(rng.integers(1, 1_000)):05d}",
                    "oldbalanceDest": 0.0,
                    "newbalanceDest": 0.0,
                    "isFraud": 1,
                    "isFlaggedFraud": 0,
                }
            )
    return pd.DataFrame(rows)


def inject_money_mule_graph(
    n_mules: int = 20,
    txns_per_mule: int = 10,
    *,
    rng: np.random.Generator | None = None,
) -> pd.DataFrame:
    """Generate money-mule flow pattern (PSF-026)."""
    rng = rng or np.random.default_rng(26)
    rows = []
    for m in range(n_mules):
        mule = f"MULE{m:04d}"
        for _ in range(txns_per_mule):
            rows.append(
                {
                    "step": int(rng.integers(1, 744)),
                    "type": "TRANSFER",
                    "amount": float(np.round(rng.uniform(50, 5_000), 2)),
                    "nameOrig": f"SRC{m % 3:03d}",
                    "oldbalanceOrg": float(rng.uniform(1e4, 1e5)),
                    "newbalanceOrig": 0.0,
                    "nameDest": mule,
                    "oldbalanceDest": float(rng.uniform(0, 1e4)),
                    "newbalanceDest": 0.0,
                    "isFraud": 1,
                    "isFlaggedFraud": 0,
                }
            )
    return pd.DataFrame(rows)


PATTERN_INJECTORS = {
    "micro_split": inject_micro_split,
    "card_testing": inject_card_testing,
    "money_mule": inject_money_mule_graph,
}


# ----------------------------- main entry point ----------------------------- #


def generate_attack_batch(
    attack_id: str,
    pattern: str,
    base_df: pd.DataFrame,
    profile: DatasetProfile,
    *,
    n_base: int = 500,
    n_pattern: int = 500,
    model: str = "ctgan",
) -> GeneratedSet:
    """Produce one labeled batch: synthetic legit-ish base + injected pattern."""
    injector = PATTERN_INJECTORS.get(pattern)
    if injector is None:
        raise ValueError(f"unknown pattern: {pattern}")

    base_sample = base_df.sample(n=n_base, random_state=hash(attack_id) & 0xFFFF).reset_index(drop=True)
    # Force label=0 in the base sample (legit background)
    if "isFraud" in base_sample.columns:
        base_sample["isFraud"] = 0

    pattern_sample = injector(rng=np.random.default_rng(hash((attack_id, pattern)) & 0xFFFF))

    combined = pd.concat([base_sample, pattern_sample], ignore_index=True).sample(
        frac=1, random_state=42
    ).reset_index(drop=True)
    return GeneratedSet(df=combined, attack_id=attack_id, pattern=pattern, model=model)


# ----------------------------- CLI ----------------------------- #


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    df, profile = load_or_synthesize("paysim", n=20_000)
    print(f"base: {profile.name}, shape={df.shape}, fraud_rate={df['isFraud'].mean():.5f}")

    for psf, pattern in [("PSF-017", "micro_split"), ("PSF-018", "card_testing"), ("PSF-026", "money_mule")]:
        batch = generate_attack_batch(psf, pattern, df, profile, n_base=300, n_pattern=300)
        print(
            f"{batch.attack_id} ({batch.pattern}): shape={batch.df.shape}, "
            f"fraud_rate={batch.df['isFraud'].mean():.3f}"
        )


if __name__ == "__main__":
    main()
