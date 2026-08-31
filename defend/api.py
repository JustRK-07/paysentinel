"""
FastAPI scoring service — real-time fraud decisioning.

POST /score        — score one or many transactions (tabular)
POST /score/text   — score one or many narrative artifacts (LLM-judge)
POST /score/batch  — score a mix
GET  /health       — health + model status
GET  /metrics      — last evaluation metrics

Mirrors industry-standard real-time decisioning APIs:
  • Single transaction scoring endpoint
  • Batch scoring
  • Decision recommendation (approve / review / block)
  • Top contributing features per prediction
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .ensemble import (
    EnsembleConfig,
    blend_scores,
    decision,
    explain_with_shap,
)
from .feature_engineering import engineer_features, feature_names
from .llm_judge import judge_artifact

logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ----------------------------- schemas ----------------------------- #


class TxnRow(BaseModel):
    step: int | None = None
    type: str | None = None
    amount: float | None = None
    nameOrig: str | None = None
    oldbalanceOrg: float | None = None
    newbalanceOrig: float | None = None
    nameDest: str | None = None
    oldbalanceDest: float | None = None
    newbalanceDest: float | None = None
    isFraud: int | None = None
    TransactionDT: int | None = None
    TransactionAmt: float | None = None
    ProductCD: str | None = None
    card1: int | None = None
    card4: str | None = None
    card6: str | None = None
    P_emaildomain: str | None = None
    DeviceInfo: str | None = None


class ScoreRequest(BaseModel):
    transactions: list[TxnRow] = Field(..., min_length=1)
    threshold: float | None = None
    explain: bool = False


class ScoreRow(BaseModel):
    score: float
    decision: str
    latency_ms: float
    top_features: list[dict[str, float]] | None = None


class ScoreResponse(BaseModel):
    count: int
    avg_latency_ms: float
    rows: list[ScoreRow]


class TextScoreRequest(BaseModel):
    artifacts: list[dict[str, Any]]


class TextScoreRow(BaseModel):
    score: float
    decision: str
    reason: str
    source: str
    latency_ms: float


class TextScoreResponse(BaseModel):
    rows: list[TextScoreRow]


# ----------------------------- service ----------------------------- #


app = FastAPI(
    title="PaySentinel — Defend API",
    description="Real-time fraud decisioning service.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_CFG = EnsembleConfig()
_MODEL_CACHE: dict[str, Any] = {}


def _try_load_models() -> dict[str, Any]:
    """Lazy-load trained models; return what's available."""
    cache: dict[str, Any] = {}
    model_dir = Path(__file__).parent.parent / "data" / "models"

    xgb_path = model_dir / "xgb.json"
    if xgb_path.exists():
        try:
            import xgboost as xgb

            m = xgb.XGBClassifier()
            m.load_model(str(xgb_path))
            cache["xgboost"] = m
        except Exception as e:
            logger.warning("xgb load failed: %s", e)

    lgb_path = model_dir / "lgb.txt"
    if lgb_path.exists():
        try:
            import lightgbm as lgb

            m = lgb.LGBMClassifier()
            m.booster_ = lgb.Booster(model_file=str(lgb_path))
            cache["lightgbm"] = m
        except Exception as e:
            logger.warning("lgb load failed: %s", e)

    return cache


@app.on_event("startup")
def _startup() -> None:
    global _MODEL_CACHE
    _MODEL_CACHE = _try_load_models()
    logger.info("loaded models: %s", list(_MODEL_CACHE.keys()))


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "models_loaded": list(_MODEL_CACHE.keys()),
        "ts": time.time(),
    }


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    p = RESULTS_DIR / "defend_summary.json"
    if not p.exists():
        return {"note": "no metrics yet — run `make demo`"}
    return json.loads(p.read_text())


@app.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest) -> ScoreResponse:
    if not _MODEL_CACHE:
        raise HTTPException(status_code=503, detail="no models loaded — run training first")

    cfg = EnsembleConfig()
    if req.threshold is not None:
        cfg.decision_threshold = req.threshold

    df = pd.DataFrame([t.model_dump() for t in req.transactions])
    feats = engineer_features(df)
    if feats.empty:
        raise HTTPException(status_code=400, detail="could not engineer features from input")
    fnames = feature_names()
    feat_cols = [c for c in feats.columns if c in fnames]
    X = feats[feat_cols].to_numpy()

    started = time.time()
    per_model_proba: dict[str, np.ndarray] = {}
    for name, model in _MODEL_CACHE.items():
        try:
            p = model.predict_proba(X)[:, 1]
            per_model_proba[name] = p
        except Exception as e:
            logger.warning("%s predict failed: %s", name, e)

    if not per_model_proba:
        # Fallback: heuristic
        per_model_proba["heuristic"] = (
            (feats["feature_drain_flag"].to_numpy() * 0.4)
            + (feats["feature_transfer_only_flag"].to_numpy() * 0.3)
            + np.clip(feats["feature_amount_zscore_user"].to_numpy() / 4, 0, 0.3)
        ).clip(0, 1)

    blended = blend_scores(per_model_proba, cfg)
    elapsed_ms = (time.time() - started) * 1000
    per_row_latency = elapsed_ms / max(1, len(blended))

    rows: list[ScoreRow] = []
    for i, score in enumerate(blended):
        top_features = None
        if req.explain:
            try:
                primary = _MODEL_CACHE.get("xgboost") or next(iter(_MODEL_CACHE.values()), None)
                if primary is not None:
                    top_features = explain_with_shap(primary, X[i], feat_cols)
            except Exception:
                top_features = None
        rows.append(
            ScoreRow(
                score=float(score),
                decision=decision(float(score), cfg),
                latency_ms=per_row_latency,
                top_features=top_features,
            )
        )

    return ScoreResponse(count=len(rows), avg_latency_ms=per_row_latency, rows=rows)


@app.post("/score/text", response_model=TextScoreResponse)
def score_text(req: TextScoreRequest) -> TextScoreResponse:
    rows: list[TextScoreRow] = []
    cfg = EnsembleConfig()
    for art in req.artifacts:
        started = time.time()
        v = judge_artifact(art)
        elapsed_ms = (time.time() - started) * 1000
        rows.append(
            TextScoreRow(
                score=v.score,
                decision=decision(v.score, cfg),
                reason=v.reason,
                source=v.source,
                latency_ms=elapsed_ms,
            )
        )
    return TextScoreResponse(rows=rows)


# ----------------------------- CLI ----------------------------- #


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
