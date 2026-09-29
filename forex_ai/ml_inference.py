"""Load trained Forex model artifacts and produce calibrated inference."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from forex_ai.probability import ProbabilityResult, calibrated_result, unavailable_result


@dataclass(frozen=True)
class ModelInfo:
    instrument: str
    status: str
    calibration: str
    timeframe: str
    schema_version: int
    metrics: dict


@dataclass(frozen=True)
class InferenceResult:
    probability: ProbabilityResult
    direction: str
    model: ModelInfo


def model_path(instrument: str, model_dir: str | Path = "models") -> Path:
    return Path(model_dir) / instrument.replace("/", "") / "model.json"


def load_model(instrument: str, model_dir: str | Path = "models") -> dict:
    path = model_path(instrument, model_dir)
    if not path.exists():
        raise FileNotFoundError(f"model artifact not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def infer_from_features(
    instrument: str,
    features: dict[str, float],
    *,
    model_dir: str | Path = "models",
) -> InferenceResult:
    payload = load_model(instrument, model_dir)
    names = payload["features"]
    missing = [name for name in names if name not in features]
    if missing:
        raise ValueError(f"missing model features: {missing}")
    if payload.get("calibration") != "platt_sigmoid":
        raise ValueError("unsupported calibration method")
    x = np.asarray([float(features[name]) for name in names], dtype=float)
    mean = np.asarray(payload["scaler_mean"], dtype=float)
    scale = np.asarray(payload["scaler_scale"], dtype=float)
    coef = np.asarray(payload["model_coef"], dtype=float)
    if len(x) != len(mean) or len(x) != len(scale) or len(x) != len(coef):
        raise ValueError("model feature dimensions do not match")
    if not np.isfinite(x).all() or (scale <= 0).any():
        raise ValueError("invalid feature values or model scale")
    decision = float(np.dot((x - mean) / scale, coef) + payload["model_intercept"])
    probability = calibrated_result(
        decision,
        intercept=payload["calibration_intercept"],
        coefficient=payload["calibration_coef"],
    )
    direction = (
        "bullish" if probability.bullish_probability >= 0.5
        else "bearish"
    )
    info = ModelInfo(
        instrument=payload["instrument"],
        status=payload["status"],
        calibration=payload["calibration"],
        timeframe=payload["timeframe"],
        schema_version=payload["schema_version"],
        metrics=payload["metrics"],
    )
    return InferenceResult(probability, direction, info)


def unavailable_inference(instrument: str) -> InferenceResult:
    info = ModelInfo(instrument, "model_unavailable", "none", "N/A", 0, {})
    return InferenceResult(unavailable_result(), "neutral", info)
