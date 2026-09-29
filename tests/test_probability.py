from forex_ai.probability import calibrated_result, platt_probability, unavailable_result


def test_platt_probability_is_bounded():
    value = platt_probability(0.0, 0.0, 1.0)
    assert value == 0.5


def test_calibrated_result_complements_probabilities():
    result = calibrated_result(1.0, intercept=0.0, coefficient=1.0)
    assert 0 < result.bullish_probability < 1
    assert result.bullish_probability + result.bearish_probability == 1.0
    assert result.calibrated is True


def test_unavailable_probability_is_explicit():
    result = unavailable_result()
    assert result.bullish_probability is None
    assert result.bearish_probability is None
    assert result.calibrated is False
