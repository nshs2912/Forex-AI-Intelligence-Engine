"""Deterministic live-readiness checks for Forex model artifacts.

This module deliberately does not manufacture approval. It evaluates evidence
already present in model artifacts and requires an explicit, auditable approval
record before a model can be marked approved_for_live.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path

from forex_ai.feature_engineering import FEATURES


# Conservative software gates. These are acceptance criteria for this DSS,
# not claims that a model meeting them will be profitable.
MIN_TEST_ROWS = 250
MIN_ROC_AUC = 0.55
MAX_BRIER = 0.25
MIN_PR_AUC_MARGIN = 0.0
MAX_MODEL_AGE_DAYS = 365


@dataclass(frozen=True)
class ValidationResult:
    instrument: str
    passed: bool
    checks: dict[str, bool]
    reasons: tuple[str, ...]


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def validate_model_artifact(path: str | Path, *, as_of: date | None = None) -> ValidationResult:
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    metrics = payload.get("metrics", {})
    instrument = str(payload.get("instrument", path.parent.name))

    checks: dict[str, bool] = {}
    reasons: list[str] = []

    checks["schema"] = payload.get("schema_version") == 1
    checks["calibration"] = payload.get("calibration") == "platt_sigmoid"
    checks["feature_parity"] = payload.get("features") == FEATURES
    checks["chronological_metrics"] = (
        int(metrics.get("train_rows", 0)) >= 100
        and int(metrics.get("calibration_rows", 0)) >= 100
        and int(metrics.get("test_rows", 0)) >= MIN_TEST_ROWS
    )
    checks["roc_auc"] = float(metrics.get("roc_auc", 0.0)) >= MIN_ROC_AUC
    checks["brier"] = float(metrics.get("brier_score", 1.0)) <= MAX_BRIER

    positive_rate = float(metrics.get("test_positive_rate", 0.0))
    pr_auc = float(metrics.get("pr_auc", 0.0))
    checks["pr_auc_vs_baseline"] = pr_auc >= positive_rate + MIN_PR_AUC_MARGIN

    end_text = metrics.get("dataset_end")
    fresh = False
    if end_text:
        reference = as_of or date.today()
        age_days = (reference - _parse_date(end_text)).days
        fresh = 0 <= age_days <= MAX_MODEL_AGE_DAYS
    checks["data_recency"] = fresh

    if payload.get("status") == "revoked":
        checks["not_revoked"] = False
    else:
        checks["not_revoked"] = True

    for name, ok in checks.items():
        if not ok:
            reasons.append(name)

    return ValidationResult(instrument, all(checks.values()), checks, tuple(reasons))


def validate_all_models(model_dir: str | Path = "models", *, as_of: date | None = None) -> list[ValidationResult]:
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
