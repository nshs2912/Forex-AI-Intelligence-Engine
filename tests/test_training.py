from pathlib import Path

import pandas as pd

from forex_ai.training.train_forex import FEATURES, make_dataset


def test_feature_dataset_has_expected_columns():
    dates = pd.date_range("2020-01-01", periods=40, freq="D", tz="UTC")
    close = pd.Series([1.0 + i * 0.001 for i in range(40)])
    frame = pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": close * 1.001,
            "low": close * 0.999,
            "close": close,
            "tick_volume": 100,
        }
    )
    result = make_dataset(frame, horizon=5, threshold=0.001)
    assert set(FEATURES).issubset(result.columns)
    assert "label" in result
    assert set(result["label"].unique()).issubset({0, 1})


def test_training_module_exists():
    assert Path("forex_ai/training/train_forex.py").exists()
