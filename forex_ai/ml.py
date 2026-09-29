"""ML-facing probability contracts."""
from __future__ import annotations

def probability_to_direction(bullish_probability: float, bearish_probability: float, *, neutral_band: float=0.10) -> float:
    if not 0 <= bullish_probability <= 1 or not 0 <= bearish_probability <= 1:
        raise ValueError("probabilities must be between 0 and 1")
    if bullish_probability + bearish_probability > 1 + 1e-9:
        raise ValueError("probabilities cannot sum above 1")
    score = bullish_probability - bearish_probability
    return 0.0 if abs(score) < neutral_band else max(-1.0, min(1.0, score))

def confidence_from_probabilities(bullish_probability: float, bearish_probability: float) -> float:
    confidence = abs(bullish_probability - bearish_probability)
    return round(max(0.0, min(1.0, confidence)), 12)
