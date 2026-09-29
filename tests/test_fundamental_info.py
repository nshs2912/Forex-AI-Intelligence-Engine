from forex_ai.fundamental_info import FUNDAMENTAL_INDICATORS, fundamental_inputs_for


def test_fundamental_indicator_catalog_is_explicit():
    assert "Interest Rate / Central Bank" in FUNDAMENTAL_INDICATORS
    assert "Economic Calendar" in FUNDAMENTAL_INDICATORS
    assert all(item["source_status"] for item in FUNDAMENTAL_INDICATORS.values())


def test_pair_fundamental_drivers_are_available():
    result = fundamental_inputs_for("EUR/USD")
    assert result["status"] == "reference_only"
    assert "ECB" in result["drivers"]


def test_fundamental_sources_have_auditable_links():
    from forex_ai.fundamental_info import fundamental_sources_for

    sources = fundamental_sources_for("EUR/USD")
    assert sources
    assert any(item["source_type"] == "official" for item in sources)
    assert any(item["source_type"] == "news" for item in sources)
    assert all(item["url"].startswith("https://") for item in sources)
    assert all(item["evidence_id"] for item in sources)


def test_unknown_instrument_gets_general_sources():
    from forex_ai.fundamental_info import fundamental_sources_for

    sources = fundamental_sources_for("UNKNOWN")
    assert any(item["currency"] == "MULTI" for item in sources)
