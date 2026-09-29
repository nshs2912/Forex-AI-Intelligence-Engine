import numpy as np
import pandas as pd

from forex_ai.feature_engineering import FEATURES
from forex_ai.training.train_forex import make_dataset


def _ohlc(rows=80):
    dates = pd.date_range("2020-01-01", periods=rows, freq="D", tz="UTC")
    close = 1.0 + np.linspace(0.0, 0.25, rows)
    return pd.DataFrame(
        {
            "date": dates,
            "open": close - 0.002,
            "high": close + 0.004,
            "low": close - 0.004,
            "close": close,
        }
    )


def test_training_dataset_uses_shared_feature_contract():
    dataset = make_dataset(_ohlc())
    assert all(feature in dataset.columns for feature in FEATURES)
    assert list(FEATURES) == [
        "ret_1", "ret_5", "ret_10", "ret_20",
        "vol_10", "vol_20", "range_pct",
    ]
    assert set(dataset["label"].unique()).issubset({0, 1})


def test_training_dataset_rejects_invalid_parameters():
    frame = _ohlc()
    try:
        make_dataset(frame, horizon=0)
    except ValueError:
        pass
    else:
        raise AssertionError("horizon=0 must be rejected")

    try:
        make_dataset(frame, threshold=0)
    except ValueError:
        pass
    else:
        raise AssertionError("threshold=0 must be rejected")
