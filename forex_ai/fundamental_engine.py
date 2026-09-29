"""Validated live fundamental intelligence from a Trading Economics calendar feed.

The engine deliberately separates provider availability from score calculation.
No API credential means UNAVAILABLE; missing events are never converted to zero.
The score is a transparent heuristic based on actual-vs-forecast surprise,
event importance, and freshness. It is decision-support evidence, not a
probability or an autonomous trading instruction.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
import os
from urllib.parse import quote
from urllib.request import Request, urlopen
import json

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    st = None

TE_URL = "https://api.tradingeconomics.com/calendar/country"
PAIR_CURRENCIES = {
    "EUR/USD": ("Euro Area", "United States"),
    "USD/JPY": ("United States", "Japan"),
    "GBP/USD": ("United Kingdom", "United States"),
    "AUD/USD": ("Australia", "United States"),
    "USD/CHF": ("United States", "Switzerland"),
    "USD/CAD": ("United States", "Canada"),
    "NZD/USD": ("New Zealand", "United States"),
}
CURRENCY_CODES = {
    "Euro Area": "EUR",
    "United States": "USD",
    "United Kingdom": "GBP",
    "Japan": "JPY",
    "Australia": "AUD",
    "Switzerland": "CHF",
    "Canada": "CAD",
    "New Zealand": "NZD",
}

# Transparent first-order economic intuition. Events outside these groups
# contribute no directional score rather than being guessed.
POLARITY_RULES = {
    "interest": 1.0,
    "rate": 1.0,
    "gdp": 1.0,
    "growth": 1.0,
    "pmi": 1.0,
    "retail": 1.0,
    "industrial": 1.0,
    "production": 1.0,
    "employment": 1.0,
    "payroll": 1.0,
    "wage": 1.0,
    "income": 1.0,
    "trade": 1.0,
    "exports": 1.0,
    "imports": -1.0,
    "unemployment": -1.0,
    "jobless": -1.0,
    "inflation": 1.0,
    "cpi": 1.0,
    "ppi": 1.0,
    "confidence": 1.0,
    "sentiment": 1.0,
}

@dataclass(frozen=True)
class FundamentalResult:
    score: float | None
    base_currency_score: float | None
    quote_currency_score: float | None
    status: str
    provider: str
    evidence_count: int
    fresh_evidence: int
    components: dict[str, float]
    evidence: tuple[dict[str, object], ...]
    message: str

class FundamentalDataError(RuntimeError):
    """Raised when a configured fundamental provider cannot be read."""

def _clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))

def _secret(name: str) -> str:
    value = ""
    if st is not None:
        try:
            value = str(st.secrets.get(name, "")).strip()
        except Exception:
            value = ""
    return value or os.getenv(name, "").strip()

def _number(value: object) -> float | None:
    if value in (None, "", "-", "null"):
        return None
    text = str(value).strip().replace(",", "")
    for suffix in ("%", "K", "M", "B", "T"):
        if text.endswith(suffix):
            text = text[:-1]
            break
    try:
        return float(text)
    except ValueError:
        return None

def _polarity(event: str) -> float:
    text = event.lower()
    for keyword, value in POLARITY_RULES.items():
        if keyword in text:
            return value
    return 0.0

def _event_score(event: dict[str, object], now: datetime) -> float | None:
    actual = _number(event.get("Actual"))
    forecast = _number(event.get("Forecast"))
    if actual is None or forecast is None:
        return None
    polarity = _polarity(str(event.get("Event") or event.get("Category") or ""))
    if polarity == 0:
        return None
    baseline = max(abs(forecast), abs(_number(event.get("Previous")) or 0.0), 1.0)
    surprise = (actual - forecast) / baseline
    importance = max(1.0, min(3.0, float(event.get("Importance") or 1)))
    stamp = _parse_datetime(event.get("Date"))
    age_hours = max(0.0, (now - stamp).total_seconds() / 3600.0)
    freshness = math.exp(-age_hours / 72.0)
    return _clamp(math.tanh(surprise * 4.0) * polarity * (0.75 + 0.25 * importance) * freshness)

def _parse_datetime(value: object) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return datetime.now(timezone.utc)
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)

def _fetch_country(country: str, start: datetime, end: datetime, timeout: float) -> list[dict[str, object]]:
    api_key = _secret("TRADING_ECONOMICS_API_KEY")
    if not api_key:
        raise FundamentalDataError(
            "TRADING_ECONOMICS_API_KEY is not configured. Fundamental score remains unavailable."
        )
    url = (
        f"{TE_URL}/{quote(country)}/{start:%Y-%m-%d}/{end:%Y-%m-%d}"
        f"?c={quote(api_key)}&f=json"
    )
    request = Request(url, headers={"User-Agent": "Forex-AI-Intelligence-Engine/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise FundamentalDataError(f"Fundamental provider request failed: {exc}") from exc
    if not isinstance(payload, list):
        raise FundamentalDataError("Fundamental provider returned an invalid calendar payload")
    return [item for item in payload if isinstance(item, dict)]

def _currency_score(
    events: list[dict[str, object]], now: datetime
) -> tuple[float | None, int, int, list[dict[str, object]]]:
    weighted: list[tuple[float, float, dict[str, object]]] = []
    for event in events:
        score = _event_score(event, now)
        if score is None:
            continue
        importance = max(1.0, min(3.0, float(event.get("Importance") or 1)))
        stamp = _parse_datetime(event.get("Date"))
        age_hours = max(0.0, (now - stamp).total_seconds() / 3600.0)
        freshness = math.exp(-age_hours / 72.0)
        weight = importance * freshness
        evidence = {
            "event": event.get("Event") or event.get("Category"),
            "date": event.get("Date"),
            "actual": event.get("Actual"),
            "forecast": event.get("Forecast"),
            "previous": event.get("Previous"),
            "importance": event.get("Importance"),
            "source": event.get("Source"),
            "source_url": event.get("SourceURL"),
            "score": round(score, 4),
        }
        weighted.append((score, weight, evidence))
    if not weighted:
        return None, 0, 0, []
    denominator = sum(weight for _, weight, _ in weighted)
    value = sum(score * weight for score, weight, _ in weighted) / denominator
    fresh = sum(
        1 for _, _, evidence in weighted
        if (now - _parse_datetime(evidence["date"])).total_seconds() <= 72 * 3600
    )
    evidence = [item[2] for item in sorted(weighted, key=lambda x: x[1], reverse=True)]
    return _clamp(value), len(weighted), fresh, evidence

def fetch_fundamental_score(
    instrument: str,
    *,
    lookback_days: int = 7,
    timeout: float = 10.0,
    now: datetime | None = None,
) -> FundamentalResult:
    """Fetch recent macro releases and calculate a pair-relative score."""
    if instrument not in PAIR_CURRENCIES:
        return FundamentalResult(
            None, None, None, "UNAVAILABLE", "Trading Economics",
            0, 0, {}, (), "Instrument has no mapped macro currency pair."
        )
    current = now or datetime.now(timezone.utc)
    start = current - timedelta(days=max(1, lookback_days))
    countries = PAIR_CURRENCIES[instrument]
    try:
        base_events = _fetch_country(countries[0], start, current, timeout)
        quote_events = _fetch_country(countries[1], start, current, timeout)
    except FundamentalDataError as exc:
        return FundamentalResult(
            None, None, None, "UNAVAILABLE", "Trading Economics",
            0, 0, {}, (), str(exc)
        )

    base, base_count, base_fresh, base_evidence = _currency_score(base_events, current)
    quote, quote_count, quote_fresh, quote_evidence = _currency_score(quote_events, current)
    if base is None or quote is None:
        return FundamentalResult(
            None, base, quote, "DEGRADED", "Trading Economics",
            base_count + quote_count, base_fresh + quote_fresh,
            {"base": base or 0.0, "quote": quote or 0.0},
            tuple(base_evidence + quote_evidence),
            "Insufficient directional macro evidence for both currencies."
        )

    score = _clamp(base - quote)
    return FundamentalResult(
        score, base, quote, "LIVE", "Trading Economics",
        base_count + quote_count, base_fresh + quote_fresh,
        {"base": base, "quote": quote, "relative": score},
        tuple(base_evidence + quote_evidence),
        "Live macro surprise score from completed economic releases."
    )
