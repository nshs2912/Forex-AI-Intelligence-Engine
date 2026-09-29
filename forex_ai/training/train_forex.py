"""Train a time-ordered, calibrated binary Forex direction model.

Training and inference share the same OHLC feature contract. Artifacts remain
trained_not_approved_for_live until independent validation, paper evidence,
and explicit human approval are present.
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


def make_dataset(
    df: pd.DataFrame, *, horizon: int = 5, threshold: float = 0.005
) -> pd.DataFrame:
    """Build a leakage-safe labeled dataset from completed OHLC bars."""
    if horizon < 1:
        raise ValueError("horizon must be >= 1")
    if threshold <= 0:
        raise ValueError("threshold must be > 0")

    out = build_features(df)
    forward_return = out["close"].shift(-horizon) / out["close"] - 1.0
    out["label"] = np.where(
        forward_return >= threshold,
        1,
        np.where(forward_return <= -threshold, 0, np.nan),
    )
    out = out.dropna(subset=FEATURES + ["label"]).copy()
    out["label"] = out["label"].astype(int)
    return out


def _periods(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = df[df["date"] < "2019-01-01"]
    calibration = df[
        (df["date"] >= "2019-01-01") & (df["date"] < "2021-01-01")
    ]
    test = df[df["date"] >= "2021-01-01"]
    if min(len(train), len(calibration), len(test)) < 100:
        raise ValueError("insufficient rows in chronological train/calibration/test periods")
    return train, calibration, test


def train_symbol(symbol: str, output_dir: Path) -> dict:
    raw = load_data(symbol)
    dataset = make_dataset(raw)
    train, calibration, test = _periods(dataset)

    scaler = StandardScaler().fit(train[FEATURES])
    x_train = scaler.transform(train[FEATURES])
    x_cal = scaler.transform(calibration[FEATURES])
    x_test = scaler.transform(test[FEATURES])

    model = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)
    model.fit(x_train, train["label"])

    cal_score = model.decision_function(x_cal).reshape(-1, 1)
    calibrator = LogisticRegression(max_iter=2000, random_state=42)
    calibrator.fit(cal_score, calibration["label"])

    test_score = model.decision_function(x_test)
    probability = _sigmoid(
        calibrator.intercept_[0] + calibrator.coef_[0, 0] * test_score
    )
    prediction = (probability >= 0.5).astype(int)
    y_test = test["label"].to_numpy()

    metrics = {
        "roc_auc": float(roc_auc_score(y_test, probability)),
        "pr_auc": float(average_precision_score(y_test, probability)),
        "brier_score": float(brier_score_loss(y_test, probability)),
        "accuracy": float(accuracy_score(y_test, prediction)),
        "precision": float(precision_score(y_test, prediction, zero_division=0)),
        "recall": float(recall_score(y_test, prediction, zero_division=0)),
        "train_rows": int(len(train)),
        "calibration_rows": int(len(calibration)),
        "test_rows": int(len(test)),
        "test_positive_rate": float(y_test.mean()),
        "dataset_start": str(raw["date"].min().date()),
        "dataset_end": str(raw["date"].max().date()),
        "data_source": str(raw.attrs.get("data_source", "unknown")),
        "horizon_bars": 5,
        "threshold": 0.005,
    }

    model_payload = {
        "schema_version": 1,
        "instrument": symbol,
        "timeframe": "1D",
        "model_type": "logistic_regression",
        "calibration": "platt_sigmoid",
        "features": list(FEATURES),
        "label": {
            "type": "binary_direction",
            "horizon_bars": 5,
            "threshold": 0.005,
            "positive": "forward_return >= +0.5%",
            "negative": "forward_return <= -0.5%",
            "neutral_moves_excluded": True,
        },
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "model_coef": model.coef_[0].tolist(),
        "model_intercept": float(model.intercept_[0]),
        "calibration_coef": float(calibrator.coef_[0, 0]),
        "calibration_intercept": float(calibrator.intercept_[0]),
        "metrics": metrics,
        "status": "trained_not_approved_for_live",
    }

    symbol_dir = output_dir / symbol.replace("/", "")
    symbol_dir.mkdir(parents=True, exist_ok=True)
    (symbol_dir / "model.json").write_text(
        json.dumps(model_payload, indent=2), encoding="utf-8"
    )
    (symbol_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    return model_payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="EUR/USD", choices=sorted(SYMBOLS))
    parser.add_argument("--output-dir", default="models")
    args = parser.parse_args()
    result = train_symbol(args.symbol, Path(args.output_dir))
    print(
        json.dumps(
            {"instrument": args.symbol, "metrics": result["metrics"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
