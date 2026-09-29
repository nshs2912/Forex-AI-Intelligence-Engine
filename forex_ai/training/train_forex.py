"""Train a time-ordered, calibrated binary Forex direction model.

The training job downloads a public daily OHLC dataset, builds lagged features,
keeps chronological train/calibration/test periods disjoint, fits logistic
regression, then fits a separate Platt sigmoid calibrator on the calibration
period. Model parameters are exported as JSON so the dashboard does not need
pickle/joblib artifacts.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

from forex_ai.feature_engineering import FEATURES, build_features
from forex_ai.market_data import fetch_daily_history

DATA_BASE = "https://raw.githubusercontent.com/nktcodes/Forex-Data/main/"
SYMBOLS = {
    "EUR/USD": "EUR_USD.csv",
    "GBP/USD": "GBP_USD.csv",
    "USD/JPY": "USD_JPY.csv",
    "AUD/USD": "AUD_USD.csv",
    "USD/CHF": "USD_CHF.csv",
    "USD/CAD": "USD_CAD.csv",
    "NZD/USD": "NZD_USD.csv",
}


def _sigmoid(x: np.ndarray | float) -> np.ndarray | float:
    if isinstance(x, np.ndarray):
        out = np.empty_like(x, dtype=float)
        positive = x >= 0
        out[positive] = 1.0 / (1.0 + np.exp(-x[positive]))
        exp_x = np.exp(x[~positive])
        out[~positive] = exp_x / (1.0 + exp_x)
        return out
    return 1.0 / (1.0 + math.exp(-x)) if x >= 0 else math.exp(x) / (1.0 + math.exp(x))


def load_data(symbol: str) -> pd.DataFrame:
    if symbol not in SYMBOLS:
        raise ValueError(f"unsupported symbol: {symbol}")

    # Live training mode uses the same provider family as dashboard inference.
    # It is opt-in so ordinary CI remains deterministic without secrets.
    if os.getenv("FOREX_TRAINING_DATA_SOURCE", "").strip().lower() == "live":
        frame = fetch_daily_history(symbol, outputsize=5000)
        frame["tick_volume"] = pd.to_numeric(
            frame.get("tick_volume", 0.0), errors="coerce"
        ).fillna(0.0)
        frame.attrs["data_source"] = "Twelve Data"
        return frame.dropna(subset=["open", "high", "low", "close"]).copy()

    url = DATA_BASE + SYMBOLS[symbol]
    with urlopen(url, timeout=30) as response:
        df = pd.read_csv(response)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    required = {"date", "open", "high", "low", "close"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    for column in ["open", "high", "low", "close"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    if "tick_volume" not in df:
        df["tick_volume"] = 0.0
    df["tick_volume"] = pd.to_numeric(df["tick_volume"], errors="coerce").fillna(0.0)
    df.attrs["data_source"] = "nktcodes/Forex-Data"
    return df.dropna(subset=["open", "high", "low", "close"]).copy()

