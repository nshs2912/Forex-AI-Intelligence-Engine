"""Probability and calibration utilities for the trading signal engine."""
from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ProbabilityResult:
    bullish_probability: float | None
    bearish_probability: float | None
    calibrated: bool
    method: str
    status: str


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def platt_probability(score: float, intercept: float, coefficient: float) -> float:
    """Convert a model score to a calibrated binary probability.

    intercept/coefficient must be fitted on a held-out calibration set.
    """
    if not math.isfinite(score) or not math.isfinite(intercept) or not math.isfinite(coefficient):
        raise ValueError("score and calibration parameters must be finite")
    return sigmoid(intercept + coefficient * score)


def calibrated_result(score: float, *, intercept: float, coefficient: float) -> ProbabilityResult:
    bullish = platt_probability(score, intercept, coefficient)
    return ProbabilityResult(
        bullish_probability=bullish,
        bearish_probability=1.0 - bullish,
        calibrated=True,
        method="Platt sigmoid",
        status="calibrated",
    )


def unavailable_result() -> ProbabilityResult:
    """Explicit result used until a trained/calibrated model is supplied."""
    return ProbabilityResult(
        bullish_probability=None,
        bearish_probability=None,
        calibrated=False,
        method="none",
        status="not_calibrated",
    )
