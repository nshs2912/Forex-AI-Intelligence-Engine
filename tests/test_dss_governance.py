from forex_ai.dss_governance import assess_dss

def test_unapproved_model_is_not_live_ready():
    result = assess_dss(
        model_status="trained_not_approved_for_live",
        calibrated=True, data_fresh=True, feature_parity=True,
        model_metrics_available=True, risk_controls_ok=True,
        validation_passed=True, approval_record_valid=True,
    )
    assert result.ready is False
    assert result.status == "GOVERNED / NOT LIVE"

def test_paper_model_is_not_live_ready():
    result = assess_dss(
        model_status="validated_for_paper",
        calibrated=True, data_fresh=True, feature_parity=True,
        model_metrics_available=True, risk_controls_ok=True,
        validation_passed=True, approval_record_valid=False,
    )
    assert result.ready is False

def test_all_live_gates_are_required():
    result = assess_dss(
        model_status="approved_for_live",
        calibrated=True, data_fresh=True, feature_parity=True,
        model_metrics_available=True, risk_controls_ok=True,
        validation_passed=True, approval_record_valid=True,
    )
    assert result.ready is True

def test_approval_without_validation_is_blocked():
    result = assess_dss(
        model_status="approved_for_live",
        calibrated=True, data_fresh=True, feature_parity=True,
        model_metrics_available=True, risk_controls_ok=True,
        validation_passed=False, approval_record_valid=True,
    )
    assert result.ready is False
