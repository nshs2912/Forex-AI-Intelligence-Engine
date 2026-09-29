import pandas as pd

from forex_ai.feature_engineering import build_features


def test_completed_daily_bar_feature_pipeline_excludes_partial_bar_by_caller():
    dates = pd.date_range("2026-01-01", periods=40, freq="D", tz="UTC")
    frame = pd.DataFrame({
        "date": dates,
        "open": [1.0 + i * 0.001 for i in range(40)],
        "high": [1.002 + i * 0.001 for i in range(40)],
        "low": [0.998 + i * 0.001 for i in range(40)],
        "close": [1.0 + i * 0.001 for i in range(40)],
        "tick_volume": [100.0] * 40,
    })
    completed = frame[frame["date"].dt.date < dates[-1].date()]
    features = build_features(completed)
    assert features["date"].max() < dates[-1]
