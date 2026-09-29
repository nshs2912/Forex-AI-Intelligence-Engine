from datetime import datetime, timezone
from unittest.mock import patch

from forex_ai.fundamental_engine import (
    _event_score,
    _currency_score,
    fetch_fundamental_score,
)


def test_event_score_rewards_positive_growth_surprise():
    now = datetime(2026, 9, 29, tzinfo=timezone.utc)
    event = {
        "Event": "GDP Growth Rate",
        "Actual": "3.0%",
        "Forecast": "2.0%",
        "Previous": "1.5%",
        "Importance": 3,
        "Date": "2026-09-29T10:00:00+00:00",
    }
    assert _event_score(event, now) > 0


def test_currency_score_ignores_events_without_forecast():
    now = datetime(2026, 9, 29, tzinfo=timezone.utc)
    events = [
        {
            "Event": "GDP Growth",
            "Actual": "3.0%",
            "Forecast": "2.0%",
            "Previous": "1.5%",
            "Importance": 3,
            "Date": "2026-09-29T10:00:00+00:00",
        },
        {
            "Event": "Speech",
            "Actual": "",
            "Forecast": "",
            "Importance": 3,
            "Date": "2026-09-29T11:00:00+00:00",
        },
    ]
    score, count, fresh, evidence = _currency_score(events, now)
    assert score is not None
    assert count == 1
    assert fresh == 1
    assert len(evidence) == 1


def test_missing_provider_key_is_unavailable():
    with patch("forex_ai.fundamental_engine._secret", return_value=""):
        result = fetch_fundamental_score("EUR/USD")
    assert result.status == "UNAVAILABLE"
    assert result.score is None


def test_pair_score_is_base_minus_quote():
    now = datetime(2026, 9, 29, tzinfo=timezone.utc)
    base = [{"Event": "GDP Growth", "Actual": "3", "Forecast": "2", "Previous": "1", "Importance": 3, "Date": "2026-09-29T10:00:00+00:00"}]
    quote = [{"Event": "GDP Growth", "Actual": "1", "Forecast": "2", "Previous": "2", "Importance": 3, "Date": "2026-09-29T10:00:00+00:00"}]
    with patch("forex_ai.fundamental_engine._fetch_country", side_effect=[base, quote]):
        result = fetch_fundamental_score("EUR/USD", now=now)
    assert result.status == "LIVE"
    assert result.score > 0
    assert result.base_currency_score > result.quote_currency_score


def test_news_score_is_included_when_live_news_is_available():
    now = datetime(2026, 9, 29, tzinfo=timezone.utc)
    base = [{"Event": "GDP Growth", "Actual": "3", "Forecast": "2", "Previous": "1", "Importance": 3, "Date": "2026-09-29T10:00:00+00:00"}]
    quote = [{"Event": "GDP Growth", "Actual": "1", "Forecast": "2", "Previous": "2", "Importance": 3, "Date": "2026-09-29T10:00:00+00:00"}]
    with patch("forex_ai.fundamental_engine._fetch_country", side_effect=[base, quote]), patch(
        "forex_ai.fundamental_engine.fetch_live_news_score",
        return_value=(0.5, "LIVE", 2, ({"title": "Strong growth outlook", "score": 0.5},), "ok"),
    ):
        result = fetch_fundamental_score("EUR/USD", now=now)
    assert result.status == "LIVE"
    assert result.news_score == 0.5
    assert result.news_evidence_count == 2
    assert result.score is not None
    assert result.score > 0

def test_news_failure_degrades_macro_score_instead_of_zeroing_it():
    now = datetime(2026, 9, 29, tzinfo=timezone.utc)
    base = [{"Event": "GDP Growth", "Actual": "3", "Forecast": "2", "Previous": "1", "Importance": 3, "Date": "2026-09-29T10:00:00+00:00"}]
    quote = [{"Event": "GDP Growth", "Actual": "1", "Forecast": "2", "Previous": "2", "Importance": 3, "Date": "2026-09-29T10:00:00+00:00"}]
    with patch("forex_ai.fundamental_engine._fetch_country", side_effect=[base, quote]), patch(
        "forex_ai.fundamental_engine.fetch_live_news_score",
        return_value=(None, "UNAVAILABLE", 0, (), "news unavailable"),
    ):
        result = fetch_fundamental_score("EUR/USD", now=now)
    assert result.status == "DEGRADED"
    assert result.score == result.macro_score


def test_missing_macro_key_does_not_crash_news_fallback():
    with patch("forex_ai.fundamental_engine._secret", return_value=""):
        result = fetch_fundamental_score("EUR/USD")
    assert result.status == "UNAVAILABLE"
    assert result.score is None
    assert result.news_status == "UNAVAILABLE"


def test_news_provider_rate_limit_is_degraded_not_exception():
    from forex_ai.fundamental_engine import FundamentalDataError, fetch_live_news_score

    with patch(
        "forex_ai.fundamental_engine._fetch_country_news",
        side_effect=FundamentalDataError("Trading Economics news feed rate limit exceeded (HTTP 429)."),
    ):
        score, status, count, evidence, message = fetch_live_news_score("EUR/USD")
    assert score is None
    assert status == "UNAVAILABLE"
    assert count == 0
    assert evidence == ()
    assert "rate limit" in message.lower() or "unavailable" in message.lower()
