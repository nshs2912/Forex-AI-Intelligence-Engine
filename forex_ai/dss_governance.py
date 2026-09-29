"""Decision-support-system governance and live-readiness gates."""
from __future__ import annotations
from dataclasses import dataclass

LIVE_APPROVED = "approved_for_live"
PAPER_APPROVED = "validated_for_paper"
TRAINED = "trained_not_approved_for_live"
REVOKED = "revoked"

@dataclass(frozen=True)
class DSSAssessment:
    ready: bool
    status: str
    reasons: tuple[str, ...]

def assess_dss(
    *,
    model_status: str,
    calibrated: bool,
    data_fresh: bool,
    feature_parity: bool,
    model_metrics_available: bool,
    risk_controls_ok: bool,
    validation_passed: bool = False,
    approval_record_valid: bool = False,
) -> DSSAssessment:
    reasons: list[str] = []
    if model_status == LIVE_APPROVED and approval_record_valid:
        reasons.append("live approval record is present and valid")
    elif model_status == PAPER_APPROVED:
        reasons.append("model is validated for paper trading only")
    elif model_status == REVOKED:
        reasons.append("model approval is revoked")
    else:
        reasons.append("model requires validation and live-use approval")
    if not calibrated:
        reasons.append("calibrated probability unavailable")
    if not data_fresh:
        reasons.append("market data is stale or unavailable")
    if not feature_parity:
        reasons.append("training/inference feature parity is not verified")
    if not model_metrics_available:
        reasons.append("validation metrics are unavailable")
    if not risk_controls_ok:
        reasons.append("risk controls are incomplete")
    if not validation_passed:
        reasons.append("live validation gates have not passed")
    ready = (
        model_status == LIVE_APPROVED
        and approval_record_valid
        and calibrated
        and data_fresh
        and feature_parity
        and model_metrics_available
        and risk_controls_ok
        and validation_passed
    )
    status = "READY" if ready else "GOVERNED / NOT LIVE"
    return DSSAssessment(ready, status, tuple(reasons))
