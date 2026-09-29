from pathlib import Path

import json

from forex_ai.ml_inference import infer_from_features


def test_eurusd_artifact_can_be_loaded():
    if not Path("models/EURUSD/model.json").exists():
        return
    payload = json.loads(Path("models/EURUSD/model.json").read_text())
    features = {name: 0.0 for name in payload["features"]}
    result = infer_from_features("EUR/USD", features)
    assert result.probability.calibrated is True
    assert result.model.instrument == "EUR/USD"
    assert result.model.status == "trained_not_approved_for_live"


def test_inference_requires_all_features():
    if not Path("models/EURUSD/model.json").exists():
        return
    try:
        infer_from_features("EUR/USD", {})
    except ValueError as exc:
        assert "missing model features" in str(exc)
    else:
        raise AssertionError("missing features should fail")
