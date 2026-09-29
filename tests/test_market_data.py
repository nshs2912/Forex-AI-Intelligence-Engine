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
    assert quote.received_at.tzinfo is not None


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)
    from forex_ai.market_data import _api_key

    with pytest.raises(MarketDataError, match="TWELVE_DATA_API_KEY"):
        _api_key()


def test_quote_age_and_freshness_boundaries():
    from datetime import datetime, timedelta, timezone
    from forex_ai.market_data import MarketQuote, quote_age_seconds, quote_freshness

    now = datetime(2026, 9, 30, 0, 0, 0, tzinfo=timezone.utc)
    quote = MarketQuote(
        symbol="EUR/USD",
        price=1.1,
        bid=None,
        ask=None,
        timestamp=now - timedelta(seconds=45),
        source="Twelve Data",
        received_at=now,
    )
    assert quote_age_seconds(quote, now=now) == 45
    assert quote_freshness(45) == "FRESH"
    assert quote_freshness(61) == "AGING"
    assert quote_freshness(301) == "STALE"


def test_quote_age_does_not_go_negative_for_clock_skew():
    from datetime import datetime, timedelta, timezone
    from forex_ai.market_data import MarketQuote, quote_age_seconds

    now = datetime.now(timezone.utc)
    quote = MarketQuote(
        symbol="EUR/USD",
        price=1.1,
        bid=None,
        ask=None,
        timestamp=now + timedelta(seconds=10),
        source="Twelve Data",
        received_at=now,
    )
    assert quote_age_seconds(quote, now=now) == 0
