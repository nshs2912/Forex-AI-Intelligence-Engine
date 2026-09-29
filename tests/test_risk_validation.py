from forex_ai.risk_validation import validate_trade_risk


def test_valid_risk_controls():
    assert validate_trade_risk(
        risk_distance=0.01,
        reward_distance=0.02,
        risk_reward=2.0,
        position_units=1000,
        risk_pct=1.0,
    )


def test_risk_above_limit_is_blocked():
    assert not validate_trade_risk(
        risk_distance=0.01,
        reward_distance=0.02,
        risk_reward=2.0,
        position_units=1000,
        risk_pct=3.0,
    )


def test_non_positive_setup_is_blocked():
    assert not validate_trade_risk(
        risk_distance=0,
        reward_distance=0.02,
        risk_reward=2.0,
        position_units=1000,
        risk_pct=1.0,
    )
