from datetime import date
import json

from forex_ai.model_validation import validate_model_artifact


def test_current_eurusd_artifact_is_blocked_until_fresh_revalidation():
    result = validate_model_artifact("models/EURUSD/model.json", as_of=date(2026, 9, 29))
    assert result.passed is False
    assert "data_recency" in result.reasons
    assert "roc_auc" in result.reasons


def test_validation_requires_recent_data_and_performance(tmp_path):
    payload = {
        "schema_version": 1,
        "instrument": "EUR/USD",
        "calibration": "platt_sigmoid",
        "features": [
            "ret_1", "ret_5", "ret_10", "ret_20",
            "vol_10", "vol_20", "range_pct",
        ],
        "metrics": {
            "train_rows": 1000,
            "calibration_rows": 200,
            "test_rows": 300,
            "roc_auc": 0.60,
            "brier_score": 0.20,
            "pr_auc": 0.55,
            "test_positive_rate": 0.50,
            "dataset_end": "2026-09-01",
        },
        "status": "candidate_for_live",
    }
    path = tmp_path / "model.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = validate_model_artifact(path, as_of=date(2026, 9, 29))
    assert result.passed is True
