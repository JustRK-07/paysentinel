"""
Voice-script simulation (no audio synthesis — transcripts only).

We deliberately do NOT generate actual deepfake audio. Instead, we produce
labeled *call metadata* + *transcript* with markers that map to voice-deepfake
detection (cadence anomalies, liveness challenge failures, voiceprint
mismatch). The defender trains on these markers; the audio side is out of
scope for PaySentinel (privacy + IP reasons).
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import asdict, dataclass
from typing import Any

from .narrative_agents import llm_or_template, LLMConfig

logger = logging.getLogger(__name__)


VOICE_SYSTEM = (
    "Generate a JSON voice-call session for fraud red-teaming. "
    "Keys: caller_id_hash, called_party, channel (ivr|human_agent|video_call), "
    "duration_seconds, transcript (short), voice_artifacts (list of strings), "
    "liveness_challenge_passed (bool), voiceprint_match_confidence (0-1). "
    "Mark 'voice_artifacts' with deepfake tells: micro-pauses, robotic cadence, "
    "audio layer seams, breath-pattern anomaly."
)


def voice_template() -> str:
    artifact_pool = [
        "micro_pauses_every_2_3s",
        "robotic_cadence_burst",
        "audio_layer_seam_at_0.4s",
        "breath_pattern_anomaly",
        "pitch_variance_below_human_baseline",
    ]
    return json.dumps(
        {
            "caller_id_hash": f"caller_{random.randint(10000, 99999)}",
            "called_party": random.choice(["customer_support", "branch_agent", "fraud_dept", "KYC_ivr"]),
            "channel": random.choice(["ivr", "human_agent", "video_call"]),
            "duration_seconds": random.randint(45, 600),
            "transcript": "Hello — I'm calling about a flagged transaction on my account. Can you confirm my last four?",
            "voice_artifacts": random.sample(artifact_pool, k=random.randint(1, 3)),
            "liveness_challenge_passed": random.random() < 0.35,
            "voiceprint_match_confidence": round(random.uniform(0.42, 0.94), 3),
        }
    )


def generate_voice_session(cfg: LLMConfig | None = None) -> dict[str, Any]:
    text, source = llm_or_template(
        "Generate a voice-call session descriptor for fraud red-teaming.",
        VOICE_SYSTEM,
        voice_template,
        cfg,
    )
    try:
        session = json.loads(text)
    except json.JSONDecodeError:
        session = {}

    markers = {
        "channel": session.get("channel"),
        "n_voice_artifacts": len(session.get("voice_artifacts", [])),
        "liveness_passed": session.get("liveness_challenge_passed"),
        "voiceprint_confidence": session.get("voiceprint_match_confidence"),
        "duration_seconds": session.get("duration_seconds"),
    }
    return {
        "type": "voice_session",
        "session": session,
        "source": source,
        "markers": markers,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(json.dumps(generate_voice_session(), indent=2))


if __name__ == "__main__":
    main()
