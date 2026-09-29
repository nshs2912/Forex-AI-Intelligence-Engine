"""Live technical-market scoring from OHLC data."""
from __future__ import annotations

from dataclasses import dataclass
import math
import pandas as pd


@dataclass(frozen=True)
class TechnicalResult:
    score: float
    trend: float
    momentum: float
    macd: float
    volatility: float
    structure: float
    status: str
    bars: int


def _clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _sigmoid_scale(value: float, scale: float) -> float:
    if scale <= 0:
        return 0.0
    return _clamp(2.0 / (1.0 + math.exp(-value / scale)) - 1.0)


def calculate_technical_score(df: pd.DataFrame) -> TechnicalResult:
    """Calculate an explainable technical score from completed OHLC bars."""
    required = {"date", "open", "high", "low", "close"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    data = df.copy().sort_values("date").drop_duplicates("date")
    for col in ["open", "high", "low", "close"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)

    if len(data) < 60:
        return TechnicalResult(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "INSUFFICIENT_DATA", len(data))

    close = data["close"]
    high = data["high"]
    low = data["low"]

    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    trend = _sigmoid_scale(float((ema20.iloc[-1] / ema50.iloc[-1]) - 1.0), 0.003)

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi = 100.0 - (100.0 / (1.0 + rs.iloc[-1]))
    if not math.isfinite(float(rsi)):
        rsi = 50.0
    momentum = _clamp((float(rsi) - 50.0) / 25.0)

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = float(macd_line.iloc[-1] - signal_line.iloc[-1])
    macd_scale = max(float(close.iloc[-1]) * 0.001, 1e-12)
    macd_score = _sigmoid_scale(macd_hist, macd_scale)

    returns = close.pct_change()
    vol20 = float(returns.rolling(20).std().iloc[-1])
    vol_long = float(returns.rolling(60).std().iloc[-1])
    if not math.isfinite(vol20) or not math.isfinite(vol_long) or vol_long <= 0:
        volatility = 0.0
    else:
        volatility = _clamp((vol_long - vol20) / max(vol_long, 1e-12))

    recent_high = float(high.iloc[-21:-1].max())
    recent_low = float(low.iloc[-21:-1].min())
    last = float(close.iloc[-1])
    width = max(recent_high - recent_low, last * 1e-6)
    structure = _clamp(((last - recent_low) / width) * 2.0 - 1.0)

    score = _clamp(
        0.30 * trend
        + 0.20 * momentum
        + 0.20 * macd_score
        + 0.10 * volatility
        + 0.20 * structure
    )
    return TechnicalResult(
        score=score,
        trend=trend,
        momentum=momentum,
        macd=macd_score,
        volatility=volatility,
        structure=structure,
        status="LIVE",
        bars=len(data),
    )
