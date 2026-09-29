from forex_ai.fundamental_info import FUNDAMENTAL_INDICATORS, fundamental_inputs_for


def test_fundamental_indicator_catalog_is_explicit():
    assert "Interest Rate / Central Bank" in FUNDAMENTAL_INDICATORS
    assert "Economic Calendar" in FUNDAMENTAL_INDICATORS
    assert all(item["source_status"] for item in FUNDAMENTAL_INDICATORS.values())


def test_pair_fundamental_drivers_are_available():
    result = fundamental_inputs_for("EUR/USD")
    assert result["status"] == "reference_only"
    assert "ECB" in result["drivers"]
