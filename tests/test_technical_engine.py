import pandas as pd

from forex_ai.technical_engine import calculate_technical_score


def _bars(n=100):
    dates = pd.date_range("2026-01-01", periods=n, freq="D", tz="UTC")
    close = [1.0 + (i * 0.001) for i in range(n)]
    return pd.DataFrame({
        "date": dates,
        "open": close,
        "high": [v * 1.002 for v in close],
        "low": [v * 0.998 for v in close],
        "close": close,
    })


def test_technical_score_is_live_and_bounded():
    result = calculate_technical_score(_bars())
    assert result.status == "LIVE"
    assert -1.0 <= result.score <= 1.0
    assert result.bars == 100


def test_technical_score_requires_enough_bars():
    result = calculate_technical_score(_bars(20))
    assert result.status == "INSUFFICIENT_DATA"
    assert result.score == 0.0
