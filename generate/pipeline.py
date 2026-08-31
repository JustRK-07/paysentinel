"""
Generate pillar pipeline — orchestrates the full synthetic fraud dataset.

Outputs:
  • data/synthetic/transactions.parquet — labeled synthetic transactions
  • data/synthetic/narrative.parquet — labeled narrative artifacts (phishing, scripts, etc.)
  • results/fidelity/<attack_id>.json — per-attack fidelity report
  • results/generate_summary.json — top-level summary

Usage:
    python -m generate.pipeline --config configs/demo.yaml
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from .base_data import DatasetProfile, load_or_synthesize
from .fidelity_eval import evaluate
from .narrative_agents import generate_batch, LLMConfig
from .txn_generator import generate_attack_batch, GeneratedSet
from .voice_sim import generate_voice_session

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
SYNTH_DIR = DATA_DIR / "synthetic"
RESULTS_DIR = Path(__file__).parent.parent / "results"
SYNTH_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
(RESULTS_DIR / "fidelity").mkdir(exist_ok=True)

# LLM configuration — set skip_llm=True to use templates only (fast, offline)
LLM_CFG = LLMConfig(skip_llm=os.environ.get("SKIP_LLM", "1") == "1")


# ----------------------------- defaults ----------------------------- #


DEFAULT_TXN_ATTACKS: list[tuple[str, str]] = [
    ("PSF-017", "micro_split"),
    ("PSF-018", "card_testing"),
    ("PSF-026", "money_mule"),
]


DEFAULT_NARRATIVE_SPECS: dict[str, dict[str, Any]] = {
    "phishing_email": {"count": 50, "kind": "phishing_email"},
    "scam_call_script": {"count": 30, "kind": "scam_call_script"},
    "synthetic_identity": {"count": 40, "kind": "synthetic_identity"},
    "kyc_document": {"count": 40, "kind": "kyc_document"},
    "agent_trajectory": {"count": 30, "kind": "agent_trajectory"},
    "voice_session": {"count": 30, "kind": "voice_session"},  # special — uses voice_sim
}


# ----------------------------- orchestrator ----------------------------- #


@dataclass
class GenerateSummary:
    n_transactions: int
    n_narrative: int
    attacks_covered: list[str]
    fidelity_overall: float
    per_attack_fidelity: dict[str, float]
    duration_seconds: float
    notes: list[str] = field(default_factory=list)


def run_pipeline(
    *,
    base_dataset: str = "paysim",
    base_n: int = 20_000,
    txn_attacks: list[tuple[str, str]] | None = None,
    n_per_txn_attack: int = 800,
    narrative_specs: dict[str, dict[str, Any]] | None = None,
    run_fidelity: bool = True,
) -> GenerateSummary:
    """Run the full Generate pillar."""
    started = time.time()
    txn_attacks = txn_attacks or DEFAULT_TXN_ATTACKS
    narrative_specs = narrative_specs or DEFAULT_NARRATIVE_SPECS

    logger.info("loading base dataset %s (n=%d)", base_dataset, base_n)
    base_df, profile = load_or_synthesize(base_dataset, n=base_n)

    # --- transactions ---
    txn_batches: list[GeneratedSet] = []
    for attack_id, pattern in txn_attacks:
        logger.info("generating %s (%s)", attack_id, pattern)
        batch = generate_attack_batch(
            attack_id, pattern, base_df, profile, n_base=n_per_txn_attack, n_pattern=n_per_txn_attack
        )
        txn_batches.append(batch)

    txn_df = pd.concat([b.df for b in txn_batches], ignore_index=True)
    txn_out = SYNTH_DIR / "transactions.csv"
    txn_df.to_csv(txn_out, index=False)
    logger.info("wrote %d transactions to %s", len(txn_df), txn_out)

    # --- narrative ---
    narrative_rows: list[dict[str, Any]] = []
    for label, spec in narrative_specs.items():
        count = spec["count"]
        kind = spec["kind"]
        logger.info("generating %d %s artifacts", count, kind)
        if kind == "voice_session":
            for _ in range(count):
                narrative_rows.append({"label": label, **generate_voice_session(cfg=LLM_CFG)})
        else:
            for art in generate_batch(kind, count, **({"cfg": LLM_CFG} if kind != "voice_session" else {})):
                narrative_rows.append({"label": label, **art})

    narr_df = pd.DataFrame(narrative_rows)
    # Flatten markers dict
    if not narr_df.empty:
        markers_df = pd.json_normalize(narr_df["markers"]).add_prefix("marker_")
        narr_flat = pd.concat([narr_df.drop(columns=["markers"]), markers_df], axis=1)
        narr_out = SYNTH_DIR / "narrative.csv"
        narr_flat.to_csv(narr_out, index=False)
        logger.info("wrote %d narrative artifacts to %s", len(narr_flat), narr_out)
    else:
        narr_flat = narr_df
        logger.warning("no narrative artifacts produced")

    # --- fidelity ---
    fidelity_overall = 0.0
    per_attack: dict[str, float] = {}
    notes: list[str] = []
    if run_fidelity and txn_batches:
        # Use a real-sample subset for the eval base
        real_sample = base_df.sample(n=min(2000, len(base_df)), random_state=42)
        scores: list[float] = []
        for batch in txn_batches:
            # Task-level fidelity is expensive — disabled by default; enable with run_task_eval=True
            report = evaluate(real_sample, batch.df, run_task_eval=False)
            per_attack[batch.attack_id] = report.overall_score
            scores.append(report.overall_score)
            (RESULTS_DIR / "fidelity" / f"{batch.attack_id}.json").write_text(
                json.dumps(report.to_dict(), indent=2, default=str), encoding="utf-8"
            )
        fidelity_overall = sum(scores) / max(1, len(scores))
        if fidelity_overall < 0.5:
            notes.append("Overall fidelity below 0.5 — consider more base data")

    summary = GenerateSummary(
        n_transactions=len(txn_df),
        n_narrative=len(narr_flat),
        attacks_covered=[b.attack_id for b in txn_batches],
        fidelity_overall=fidelity_overall,
        per_attack_fidelity=per_attack,
        duration_seconds=time.time() - started,
        notes=notes,
    )

    (RESULTS_DIR / "generate_summary.json").write_text(
        json.dumps(asdict(summary), indent=2, default=str), encoding="utf-8"
    )
    logger.info("Generate pipeline done in %.1fs — fidelity=%.3f", summary.duration_seconds, fidelity_overall)
    return summary


# ----------------------------- CLI ----------------------------- #


def main() -> None:
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="paysim")
    parser.add_argument("--base-n", type=int, default=20_000)
    parser.add_argument("--n-per-attack", type=int, default=800)
    parser.add_argument("--no-fidelity", action="store_true")
    args = parser.parse_args()

    summary = run_pipeline(
        base_dataset=args.base,
        base_n=args.base_n,
        n_per_txn_attack=args.n_per_attack,
        run_fidelity=not args.no_fidelity,
    )
    print(json.dumps(asdict(summary), indent=2, default=str))


if __name__ == "__main__":
    main()
