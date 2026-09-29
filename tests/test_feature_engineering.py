import pandas as pd

from forex_ai.feature_engineering import FEATURES, build_features


def test_training_features_are_deterministic_and_complete():
    close = [1.0 + i * 0.001 for i in range(50)]
    frame = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=50, freq="D", tz="UTC"),
        "open": close,
        "high": [x * 1.002 for x in close],
        "low": [x * 0.998 for x in close],
        "close": close,
        "tick_volume": [100.0] * 50,
    })
    result = build_features(frame)
    assert set(FEATURES).issubset(result.columns)
    assert len(result) > 0
    assert result[FEATURES].isna().sum().sum() == 0
