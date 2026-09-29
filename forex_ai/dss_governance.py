"""Decision-support-system governance and readiness gates."""
from __future__ import annotations

from dataclasses import dataclass


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
) -> DSSAssessment:
    reasons = []
    if model_status != "trained_not_approved_for_live":
        reasons.append("model status is not explicitly governed")
    else:
        reasons.append("model requires live-use approval")
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
    # A model marked trained_not_approved_for_live is intentionally not production-ready.
    ready = (
        model_status == "approved_for_live"
        and calibrated
        and data_fresh
        and feature_parity
        and model_metrics_available
        and risk_controls_ok
    )
    status = "READY" if ready else "GOVERNED / NOT LIVE"
    return DSSAssessment(ready, status, tuple(reasons))
