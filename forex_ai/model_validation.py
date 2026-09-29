"""Deterministic live-readiness checks for Forex model artifacts.

This module evaluates evidence already present in repository artifacts. It never
creates or infers human approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
from pathlib import Path
from typing import Any

from forex_ai.feature_engineering import FEATURES

MIN_TEST_ROWS = 250
MIN_ROC_AUC = 0.55
MAX_BRIER = 0.25
MIN_PR_AUC_MARGIN = 0.0
MAX_MODEL_AGE_DAYS = 365
REQUIRED_APPROVAL_SCHEMA_VERSION = 1
REQUIRED_MODEL_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ValidationResult:
    instrument: str
    passed: bool
    checks: dict[str, bool]
    reasons: tuple[str, ...]


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _finite_number(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return number == number and abs(number) != float("inf")


def validate_model_artifact(
    path: str | Path, *, as_of: date | None = None
) -> ValidationResult:
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    metrics = payload.get("metrics", {})
    instrument = str(payload.get("instrument", path.parent.name))

    checks: dict[str, bool] = {}
    reasons: list[str] = []

    checks["schema"] = payload.get("schema_version") == REQUIRED_MODEL_SCHEMA_VERSION
    checks["calibration"] = payload.get("calibration") == "platt_sigmoid"
    checks["feature_parity"] = payload.get("features") == FEATURES

    feature_count = len(FEATURES)
    checks["parameter_shapes"] = (
        isinstance(payload.get("scaler_mean"), list)
        and isinstance(payload.get("scaler_scale"), list)
        and isinstance(payload.get("model_coef"), list)
        and len(payload["scaler_mean"]) == feature_count
        and len(payload["scaler_scale"]) == feature_count
        and len(payload["model_coef"]) == feature_count
        and all(_finite_number(x) for x in payload["scaler_mean"])
        and all(_finite_number(x) and float(x) > 0 for x in payload["scaler_scale"])
        and all(_finite_number(x) for x in payload["model_coef"])
        and _finite_number(payload.get("model_intercept"))
        and _finite_number(payload.get("calibration_coef"))
        and _finite_number(payload.get("calibration_intercept"))
    )

    checks["chronological_metrics"] = (
        int(metrics.get("train_rows", 0)) >= 100
        and int(metrics.get("calibration_rows", 0)) >= 100
        and int(metrics.get("test_rows", 0)) >= MIN_TEST_ROWS
    )

    checks["metrics_finite"] = all(
        _finite_number(metrics.get(name))
        for name in ("roc_auc", "pr_auc", "brier_score", "test_positive_rate")
    )
    checks["roc_auc"] = checks["metrics_finite"] and float(metrics.get("roc_auc", 0.0)) >= MIN_ROC_AUC
    checks["brier"] = checks["metrics_finite"] and float(metrics.get("brier_score", 1.0)) <= MAX_BRIER

    positive_rate = float(metrics.get("test_positive_rate", 0.0))
    pr_auc = float(metrics.get("pr_auc", 0.0))
    checks["pr_auc_vs_baseline"] = (
        checks["metrics_finite"]
        and 0.0 <= positive_rate <= 1.0
        and 0.0 <= pr_auc <= 1.0
        and pr_auc >= positive_rate + MIN_PR_AUC_MARGIN
    )

    end_text = metrics.get("dataset_end")
    fresh = False
    if end_text:
        try:
            reference = as_of or date.today()
            age_days = (reference - _parse_date(str(end_text))).days
            fresh = 0 <= age_days <= MAX_MODEL_AGE_DAYS
        except ValueError:
            fresh = False
    checks["data_recency"] = fresh

    checks["not_revoked"] = payload.get("status") != "revoked"

    for name, ok in checks.items():
        if not ok:
            reasons.append(name)

    return ValidationResult(instrument, all(checks.values()), checks, tuple(reasons))


def _load_json(path: str | Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def validate_approval_record(
    path: str | Path = "approval_record.json",
    *,
    expected_model_id: str | None = None,
    expected_instrument: str | None = None,
    as_of: datetime | None = None,
) -> bool:
    payload = _load_json(path)
    if payload is None:
        return False
    required = (
        payload.get("schema_version") == REQUIRED_APPROVAL_SCHEMA_VERSION
        and payload.get("decision") == "approved_for_live"
        and bool(payload.get("model_id"))
        and bool(payload.get("instrument"))
        and bool(payload.get("reviewer"))
        and bool(payload.get("reviewed_at"))
        and bool(payload.get("expiry_at"))
        and bool(payload.get("evidence_refs"))
    )
    if not required:
        return False
    if expected_model_id and payload.get("model_id") != expected_model_id:
        return False
    if expected_instrument and payload.get("instrument") != expected_instrument:
        return False

    try:
        reviewed = datetime.fromisoformat(str(payload["reviewed_at"]).replace("Z", "+00:00"))
        expiry = datetime.fromisoformat(str(payload["expiry_at"]).replace("Z", "+00:00"))
        reference = as_of or datetime.now(timezone.utc)
        if reviewed.tzinfo is None or expiry.tzinfo is None:
            return False
        if expiry <= reviewed or expiry <= reference:
            return False
    except ValueError:
        return False
    return True


def validate_paper_evidence(
    path: str | Path,
    *,
    expected_model_id: str | None = None,
    expected_instrument: str | None = None,
) -> bool:
    payload = _load_json(path)
    if payload is None:
        return False
    passed = (
        payload.get("schema_version") == 1
        and payload.get("validation_status") == "passed"
        and int(payload.get("sample_count", 0)) >= 100
        and bool(payload.get("model_id"))
        and bool(payload.get("instrument"))
        and bool(payload.get("period_start"))
        and bool(payload.get("period_end"))
        and payload.get("cost_model", {}).get("spread") is not None
        and payload.get("cost_model", {}).get("slippage") is not None
        and payload.get("human_review", {}).get("decision") == "approved_for_paper"
    )
    if not passed:
        return False
    if expected_model_id and payload.get("model_id") != expected_model_id:
        return False
    if expected_instrument and payload.get("instrument") != expected_instrument:
        return False
    return True


def validate_all_models(
    model_dir: str | Path = "models", *, as_of: date | None = None
) -> list[ValidationResult]:
    paths = sorted(Path(model_dir).glob("*/model.json"))
    if not paths:
        raise FileNotFoundError(f"no model artifacts found under {model_dir}")
    return [validate_model_artifact(path, as_of=as_of) for path in paths]


def write_report(results: list[ValidationResult], output: str | Path) -> None:
    payload = {
        "report_type": "forex_live_readiness",
        "generated_for": "decision-support-system",
        "results": [
            {
                "instrument": result.instrument,
                "passed": result.passed,
                "checks": result.checks,
                "reasons": list(result.reasons),
            }
            for result in results
        ],
        "all_models_passed": all(result.passed for result in results),
    }
    Path(output).write_text(json.dumps(payload, indent=2), encoding="utf-8")
