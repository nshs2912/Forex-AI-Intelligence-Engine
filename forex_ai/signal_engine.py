"""Explainable fusion of fundamental, technical and ML signals."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SignalResult:
    direction: str
    score: float
    confidence: float
    components: dict[str,float]

def _clamp(x: float, lo: float=-1.0, hi: float=1.0): return max(lo,min(hi,x))

def combine_signals(fundamental: float, technical: float, ml_direction: float, *, fundamental_weight: float=0.25, technical_weight: float=0.25, ml_weight: float=0.30, regime: float=0.10, risk_filter: float=0.10):
    weights=(fundamental_weight,technical_weight,ml_weight,0.10,0.10)
    if any(w<0 for w in weights): raise ValueError("weights must be non-negative")
    total=sum(weights)
    vals={"fundamental":_clamp(fundamental),"technical":_clamp(technical),"ml_direction":_clamp(ml_direction),"regime":_clamp(regime),"risk_filter":_clamp(risk_filter)}
    score=_clamp(sum(v*w for v,w in zip(vals.values(),weights))/total)
    direction="bullish" if score>0.15 else "bearish" if score<-0.15 else "neutral"
    return SignalResult(direction,score,abs(score),vals)
