"""Generation tests — verify generators produce well-formed artifacts."""

from generate.narrative_agents import (
    generate_batch,
    generate_phishing_email,
    generate_scam_call_script,
    generate_synthetic_identity,
    generate_kyc_document,
    generate_agent_trajectory,
)
from generate.voice_sim import generate_voice_session
from generate.txn_generator import generate_attack_batch
from generate.base_data import load_or_synthesize


def test_phishing_email_has_markers():
    art = generate_phishing_email()
    assert "markers" in art
    assert art["markers"]["word_count"] > 0


def test_scam_call_script_parses():
    art = generate_scam_call_script()
    assert art["markers"]["n_turns"] >= 5


def test_synthetic_identity_has_ssn():
    art = generate_synthetic_identity()
    profile = art["profile"]
    assert "ssn" in profile or "raw" in profile


def test_kyc_document_has_tells():
    art = generate_kyc_document()
    assert art["markers"]["has_visual_tells"] or art["markers"]["has_fingerprint_markers"]


def test_agent_trajectory_has_actions():
    art = generate_agent_trajectory()
    assert art["markers"]["n_actions"] > 0


def test_voice_session_has_artifacts():
    art = generate_voice_session()
    assert "markers" in art
    assert art["markers"]["channel"] is not None


def test_txn_batch_shape():
    df, profile = load_or_synthesize("paysim", n=2000)
    batch = generate_attack_batch("PSF-017", "micro_split", df, profile, n_base=100, n_pattern=50)
    assert "isFraud" in batch.df.columns
    # micro_split defaults: 5 sources × 30 per source = 150 fraud rows + 100 base = 250 total
    assert batch.df.shape[0] == 250
    assert batch.df["isFraud"].sum() > 0


def test_batch_generators():
    for kind in ["phishing_email", "scam_call_script", "synthetic_identity", "kyc_document", "agent_trajectory"]:
        out = generate_batch(kind, 3)
        assert len(out) == 3
        for art in out:
            assert "type" in art
            assert "markers" in art
