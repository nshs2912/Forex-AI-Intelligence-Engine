import pytest

from forex_ai.market_data import MarketDataError, MarketQuote, _parse_timestamp


def test_parse_timestamp_adds_utc_when_missing():
    value = _parse_timestamp("2026-09-29 08:55:00")
    assert value.tzinfo is not None


def test_unix_timestamp_is_preferred():
    from forex_ai.market_data import _parse_timestamp

    value = _parse_timestamp("2026-09-29 00:00:00", 1780272000)
    assert value.tzinfo is not None
    assert value.year == 2026


def test_market_quote_contract():
    quote = MarketQuote(
        symbol="EUR/USD",
        price=1.1,
        bid=1.0999,
        ask=1.1001,
        timestamp=_parse_timestamp("2026-09-29 08:55:00"),
        source="Twelve Data",
    )
    assert quote.symbol == "EUR/USD"
    assert quote.price > 0
    assert quote.source == "Twelve Data"


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)
    from forex_ai.market_data import _api_key

    with pytest.raises(MarketDataError, match="TWELVE_DATA_API_KEY"):
        _api_key()
