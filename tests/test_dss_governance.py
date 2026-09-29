from forex_ai.dss_governance import assess_dss


def test_unapproved_model_is_not_live_ready():
    result = assess_dss(
        model_status="trained_not_approved_for_live",
        calibrated=True,
        data_fresh=True,
        feature_parity=True,
        model_metrics_available=True,
        risk_controls_ok=True,
    )
    assert result.ready is False
    assert result.status == "GOVERNED / NOT LIVE"


def test_all_gates_are_required():
    result = assess_dss(
        model_status="approved_for_live",
        calibrated=True,
        data_fresh=True,
        feature_parity=True,
        model_metrics_available=True,
        risk_controls_ok=True,
    )
    assert result.ready is True
