"""Explainable fusion of fundamental, technical and ML signals."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SignalResult:
    direction: str
    score: float
    confidence: float
    components: dict[str, float | None]

def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))

def combine_signals(
    fundamental: float | None,
    technical: float | None,
    ml_direction: float | None,
    *,
    fundamental_weight: float = 0.25,
    technical_weight: float = 0.25,
    ml_weight: float = 0.30,
    regime: float = 0.10,
    risk_filter: float = 0.10,
) -> SignalResult:
    """Combine available intelligence while excluding unavailable feeds.

    Missing inputs are not treated as neutral. Their weights are removed from
    the denominator so an unavailable feed cannot silently bias the score.
    """
    raw = {
        "fundamental": fundamental,
        "technical": technical,
        "ml_direction": ml_direction,
        "regime": regime,
        "risk_filter": risk_filter,
    }
    weights = {
        "fundamental": fundamental_weight,
        "technical": technical_weight,
        "ml_direction": ml_weight,
        "regime": 0.10,
        "risk_filter": 0.10,
    }
    if any(weight < 0 for weight in weights.values()):
        raise ValueError("weights must be non-negative")

    available = {
        name: _clamp(float(value))
        for name, value in raw.items()
        if value is not None
    }
    total = sum(weights[name] for name in available)
    if total <= 0:
        raise ValueError("at least one weighted signal must be available")

    score = _clamp(
        sum(available[name] * weights[name] for name in available) / total
    )
    direction = "bullish" if score > 0.15 else "bearish" if score < -0.15 else "neutral"
    return SignalResult(
        direction=direction,
        score=score,
        confidence=abs(score),
        components={
            name: (available[name] if name in available else None)
            for name in raw
        },
    )
