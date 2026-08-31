"""Smoke tests — verify the package imports cleanly and basic flows work."""

import json
from pathlib import Path


def test_catalog_loads():
    from identify.threat_landscape import load_catalog
    cat = load_catalog()
    assert cat.stats["total_attacks"] == 30
    assert len(cat.attacks) == 30


def test_attack_filter():
    from identify.threat_landscape import filter_attacks, load_catalog

    cat = load_catalog()
    voice = filter_attacks(cat, surface="voice")
    assert 3 <= len(voice) <= 5
    assert all(a.surface == "voice" for a in voice)


def test_attack_lookup():
    from identify.threat_landscape import get_attack, load_catalog

    cat = load_catalog()
    a = get_attack(cat, "PSF-014")
    assert a is not None
    assert "scam" in a.name.lower() or "scam" in a.mechanics.lower()


def test_feature_engineering():
    import pandas as pd
    from defend.feature_engineering import engineer_features, feature_names

    df = pd.DataFrame(
        {
            "amount": [100, 5000, 50_000],
            "type": ["PAYMENT", "TRANSFER", "CASH_OUT"],
            "step": [1, 12, 25],
            "oldbalanceOrg": [1000, 5000, 60_000],
            "newbalanceOrig": [900, 0, 10_000],
            "nameOrig": ["A1", "A2", "A3"],
            "nameDest": ["B1", "B2", "B3"],
            "oldbalanceDest": [0, 0, 0],
            "newbalanceDest": [100, 5000, 50_000],
        }
    )
    feats = engineer_features(df)
    assert "feature_amount" in feats.columns
    assert feats.shape[0] == 3
    assert not feats.isnull().any().any()


def test_ensemble_blend():
    import numpy as np
    from defend.ensemble import blend_scores

    probs = {
        "xgboost": np.array([0.1, 0.9, 0.5]),
        "lightgbm": np.array([0.2, 0.8, 0.4]),
    }
    blended = blend_scores(probs)
    assert blended.shape == (3,)
    assert all(0 <= p <= 1 for p in blended)


def test_attack_catalog_json_valid():
    cat = json.loads(Path("identify/catalog.json").read_text())
    assert cat["stats"]["total_attacks"] == 30
    assert len(cat["attacks"]) == 30
    # All attacks have required fields
    for a in cat["attacks"]:
        assert {"id", "name", "surface", "severity", "mechanics"}.issubset(a.keys())
