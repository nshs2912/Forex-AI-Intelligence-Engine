from datetime import date, datetime, timezone
import json

from forex_ai.model_validation import (
    validate_approval_record,
    validate_model_artifact,
    validate_paper_evidence,
)


def _valid_model_payload():
    return {
        "schema_version": 1,
        "instrument": "EUR/USD",
        "calibration": "platt_sigmoid",
        "features": [
            "ret_1", "ret_5", "ret_10", "ret_20",
            "vol_10", "vol_20", "range_pct",
        ],
        "scaler_mean": [0.0] * 7,
        "scaler_scale": [1.0] * 7,
        "model_coef": [0.1] * 7,
        "model_intercept": 0.0,
        "calibration_coef": 1.0,
        "calibration_intercept": 0.0,
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


def test_current_eurusd_artifact_is_blocked_until_fresh_revalidation():
    result = validate_model_artifact(
        "models/EURUSD/model.json", as_of=date(2026, 9, 29)
    )
    assert result.passed is False
    assert "data_recency" in result.reasons
    assert "roc_auc" in result.reasons


def test_validation_requires_recent_data_and_performance(tmp_path):
    path = tmp_path / "model.json"
    path.write_text(json.dumps(_valid_model_payload()), encoding="utf-8")
    result = validate_model_artifact(path, as_of=date(2026, 9, 29))
    assert result.passed is True


def test_validation_rejects_wrong_parameter_shape(tmp_path):
    payload = _valid_model_payload()
    payload["model_coef"] = [0.1] * 6
    path = tmp_path / "model.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = validate_model_artifact(path, as_of=date(2026, 9, 29))
    assert result.passed is False
    assert "parameter_shapes" in result.reasons


def test_approval_record_requires_matching_model_and_unexpired_date(tmp_path):
    now = datetime(2026, 9, 29, 12, tzinfo=timezone.utc)
    path = tmp_path / "approval.json"
    payload = {
        "schema_version": 1,
        "decision": "approved_for_live",
        "model_id": "EURUSD",
        "instrument": "EUR/USD",
        "reviewer": "human-reviewer",
        "reviewed_at": "2026-09-29T10:00:00Z",
        "expiry_at": "2026-10-29T10:00:00Z",
        "evidence_refs": ["paper/evidence.json"],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert validate_approval_record(
        path,
        expected_model_id="EURUSD",
        expected_instrument="EUR/USD",
        as_of=now,
    )
    assert not validate_approval_record(
        path,
        expected_model_id="GBPUSD",
        expected_instrument="EUR/USD",
        as_of=now,
    )


def test_expired_approval_is_blocked(tmp_path):
    path = tmp_path / "approval.json"
    payload = {
        "schema_version": 1,
        "decision": "approved_for_live",
        "model_id": "EURUSD",
        "instrument": "EUR/USD",
        "reviewer": "human-reviewer",
        "reviewed_at": "2026-08-01T10:00:00Z",
        "expiry_at": "2026-09-01T10:00:00Z",
        "evidence_refs": ["paper/evidence.json"],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert not validate_approval_record(
        path,
        expected_model_id="EURUSD",
        expected_instrument="EUR/USD",
        as_of=datetime(2026, 9, 29, tzinfo=timezone.utc),
    )


def test_paper_evidence_requires_matching_identity(tmp_path):
    path = tmp_path / "paper.json"
    payload = {
        "schema_version": 1,
        "model_id": "EURUSD",
        "instrument": "EUR/USD",
        "period_start": "2026-01-01",
        "period_end": "2026-06-30",
        "sample_count": 250,
        "cost_model": {"spread": 0.0001, "slippage": 0.00005},
        "validation_status": "passed",
        "human_review": {"decision": "approved_for_paper"},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert validate_paper_evidence(
        path, expected_model_id="EURUSD", expected_instrument="EUR/USD"
    )
    assert not validate_paper_evidence(
        path, expected_model_id="GBPUSD", expected_instrument="EUR/USD"
    )
