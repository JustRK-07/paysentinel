"""
LLM-as-judge for narrative fraud artifacts.

Takes a phishing email, scam call transcript, or agent trajectory and outputs
a fraud probability + reasoning. The judge uses a *deterministic prompt
template* with low-temperature sampling to keep outputs stable.

Used both:
  • As an ensemble member for narrative attack vectors
  • As a 'reasoning' layer in the API response (alongside tabular score)
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import asdict, dataclass
from typing import Any

from generate.narrative_agents import llm_or_template, LLMConfig

logger = logging.getLogger(__name__)


JUDGE_SYSTEM = (
    "You are a fraud-investigation analyst. You score inbound artifacts for "
    "fraud probability 0-1 and produce a one-sentence reason. Output JSON only "
    "with keys 'score' (float 0-1) and 'reason' (string). Be conservative — "
    "false positives cost money; false negatives cost trust."
)

JUDGE_PROMPT = """
Artifact type: {artifact_type}
Markers extracted by structural analyzer: {markers}
Artifact body:
\"\"\"{body}\"\"\"

Output JSON: {{"score": <float 0-1>, "reason": "<one sentence>"}}
""".strip()


def _judge_template(artifact_type: str, markers: dict, body: str) -> str:
    """Deterministic heuristic judge — used when no API key."""
    score = 0.5
    reasons: list[str] = []

    if artifact_type == "phishing_email":
        if markers.get("has_urgency"):
            score += 0.15
            reasons.append("urgency cues")
        if markers.get("has_external_link"):
            score += 0.1
            reasons.append("external CTA link")
        if markers.get("link_domain_brand_mismatch"):
            score += 0.25
            reasons.append("brand/domain mismatch")
        if markers.get("vague_greeting"):
            score += 0.1
            reasons.append("vague greeting")

    elif artifact_type == "scam_call_script":
        if markers.get("has_urgency"):
            score += 0.15
            reasons.append("urgency cues")
        if markers.get("requests_pii"):
            score += 0.2
            reasons.append("requests PII")
        if markers.get("requests_payment_method"):
            score += 0.2
            reasons.append("requests payment")
        if markers.get("n_turns", 0) >= 8:
            score += 0.05
            reasons.append("multi-turn manipulation")

    elif artifact_type == "agent_trajectory":
        if markers.get("high_risk_actions", 0) >= 1:
            score += 0.2
            reasons.append("high-risk actions present")
        if markers.get("prompt_injection_attempts", 0) >= 1:
            score += 0.3
            reasons.append("prompt-injection attempts")
        if "checkout" in markers.get("tools_used", []):
            score += 0.1
            reasons.append("uses checkout tool")

    elif artifact_type == "voice_session":
        if not markers.get("liveness_passed"):
            score += 0.25
            reasons.append("liveness failed")
        if markers.get("voiceprint_confidence", 1) < 0.6:
            score += 0.2
            reasons.append("low voiceprint confidence")
        if markers.get("n_voice_artifacts", 0) >= 2:
            score += 0.15
            reasons.append("deepfake voice artifacts")
        if markers.get("channel") == "ivr":
            score += 0.05
            reasons.append("IVR channel")

    score = min(1.0, max(0.0, score))
    reason = "Heuristic flags: " + ", ".join(reasons) if reasons else "No strong fraud signals."
    return json.dumps({"score": score, "reason": reason})


@dataclass
class JudgeVerdict:
    score: float
    reason: str
    source: str


def judge_artifact(
    artifact: dict[str, Any],
    *,
    cfg: LLMConfig | None = None,
) -> JudgeVerdict:
    """Score one artifact."""
    cfg = cfg or LLMConfig()
    artifact_type = artifact.get("type", "unknown")
    markers = artifact.get("markers", {})
    body = (
        artifact.get("text")
        or json.dumps(artifact.get("transcript"))
        or json.dumps(artifact.get("profile"))
        or json.dumps(artifact.get("actions"))
        or json.dumps(artifact.get("session"))
        or ""
    )
    body = body[:1500]  # truncate for cost
    prompt = JUDGE_PROMPT.format(artifact_type=artifact_type, markers=markers, body=body)
    text, source = llm_or_template(
        prompt,
        JUDGE_SYSTEM,
        lambda: _judge_template(artifact_type, markers, body),
        cfg,
    )

    try:
        parsed = json.loads(text)
        score = float(parsed.get("score", 0.5))
        reason = str(parsed.get("reason", ""))
    except (json.JSONDecodeError, ValueError, TypeError):
        score = 0.5
        reason = "Parse failure — defaulted to neutral"

    score = min(1.0, max(0.0, score))
    return JudgeVerdict(score=score, reason=reason, source=source)


def judge_batch(artifacts: list[dict[str, Any]], cfg: LLMConfig | None = None) -> list[JudgeVerdict]:
    return [judge_artifact(a, cfg=cfg) for a in artifacts]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from generate.narrative_agents import generate_phishing_email, generate_scam_call_script

    for art in [
        generate_phishing_email(),
        generate_scam_call_script(),
    ]:
        v = judge_artifact(art)
        print(f"{art['type']:20s} score={v.score:.2f}  reason={v.reason[:80]}  source={v.source}")


if __name__ == "__main__":
    main()
