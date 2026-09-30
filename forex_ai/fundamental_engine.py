"""Validated live fundamental intelligence from macro and news feeds."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import math
import os
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

try:
    import streamlit as st
except ImportError:
    st = None

TE_URL = "https://api.tradingeconomics.com/calendar/country"
NEWS_URL = "https://api.tradingeconomics.com/news/country"
NEWS_TICKER_URL = "https://api.tradingeconomics.com/news/ticker"

PAIR_CURRENCIES = {
    "EUR/USD": ("Euro Area", "United States"),
    "USD/JPY": ("United States", "Japan"),
    "GBP/USD": ("United Kingdom", "United States"),
    "AUD/USD": ("Australia", "United States"),
    "USD/CHF": ("United States", "Switzerland"),
    "USD/CAD": ("United States", "Canada"),
    "NZD/USD": ("New Zealand", "United States"),
}

PRECIOUS_METALS = {
    "XAU/USD": {"ticker": "XAUUSD:CUR", "name": "Gold"},
    "XAG/USD": {"ticker": "XAGUSD:CUR", "name": "Silver"},
}

METAL_MACRO_POLARITY = {
    "interest": -1.0, "rate": -1.0, "gdp": -1.0, "growth": -1.0,
    "pmi": -1.0, "retail": -1.0, "industrial": -1.0, "production": -1.0,
    "employment": -1.0, "payroll": -1.0, "wage": -1.0, "income": -1.0,
    "unemployment": 1.0, "jobless": 1.0,
}

METAL_NEWS_POLARITY = {
    "gold rises": 1.0, "gold gains": 1.0, "gold climbs": 1.0,
    "gold advances": 1.0, "gold rallies": 1.0, "gold jumps": 1.0,
    "silver rises": 1.0, "silver gains": 1.0, "silver climbs": 1.0,
    "silver advances": 1.0, "silver rallies": 1.0, "silver jumps": 1.0,
    "safe haven": 1.0, "central bank buying": 1.0, "strong demand": 1.0,
    "supply deficit": 1.0, "geopolitical risk": 1.0, "weaker dollar": 1.0,
    "lower yields": 1.0, "rate cut": 1.0, "cuts rates": 1.0, "dovish": 1.0,
    "gold falls": -1.0, "gold drops": -1.0, "gold slips": -1.0,
    "gold declines": -1.0, "gold retreats": -1.0, "gold sinks": -1.0,
    "silver falls": -1.0, "silver drops": -1.0, "silver slips": -1.0,
    "silver declines": -1.0, "silver retreats": -1.0, "silver sinks": -1.0,
    "rate hike": -1.0, "raises rates": -1.0, "hawkish": -1.0,
    "strong dollar": -1.0, "higher yields": -1.0, "yield surge": -1.0,
    "weak demand": -1.0, "oversupply": -1.0,
}

POLARITY_RULES = {
    "interest": 1.0, "rate": 1.0, "gdp": 1.0, "growth": 1.0,
    "pmi": 1.0, "retail": 1.0, "industrial": 1.0, "production": 1.0,
    "employment": 1.0, "payroll": 1.0, "wage": 1.0, "income": 1.0,
    "trade": 1.0, "exports": 1.0, "imports": -1.0,
    "unemployment": -1.0, "jobless": -1.0, "inflation": 1.0,
    "cpi": 1.0, "ppi": 1.0, "confidence": 1.0, "sentiment": 1.0,
}

NEWS_POLARITY = {
    "hawkish": 1.0, "rate hike": 1.0, "raises rates": 1.0,
    "strong growth": 1.0, "beats expectations": 1.0,
    "beat expectations": 1.0, "strong employment": 1.0,
    "dovish": -1.0, "rate cut": -1.0, "cuts rates": -1.0,
    "weak growth": -1.0, "misses expectations": -1.0,
    "miss expectations": -1.0, "weak employment": -1.0,
    "recession": -1.0, "default": -1.0, "crisis": -1.0,
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
    macro_score: float | None = None
    news_score: float | None = None
    news_status: str = "UNAVAILABLE"
    news_evidence_count: int = 0

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

def _parse_datetime(value: object) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return datetime.now(timezone.utc)
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)

def _polarity(event: str) -> float:
    text = event.lower()
    for keyword, value in POLARITY_RULES.items():
        if keyword in text:
            return value
    return 0.0

def _event_score(event: dict[str, object], now: datetime, polarity_rules: dict[str, float] = POLARITY_RULES) -> float | None:
    actual = _number(event.get("Actual"))
    forecast = _number(event.get("Forecast"))
    if actual is None or forecast is None:
        return None
    event_name = str(event.get("Event") or event.get("Category") or "").lower()
    polarity = 0.0
    for keyword, value in polarity_rules.items():
        if keyword in event_name:
            polarity = value
            break
    if polarity == 0:
        return None
    baseline = max(abs(forecast), abs(_number(event.get("Previous")) or 0.0), 1.0)
    surprise = (actual - forecast) / baseline
    importance = max(1.0, min(3.0, float(event.get("Importance") or 1)))
    stamp = _parse_datetime(event.get("Date"))
    freshness = math.exp(-max(0.0, (now - stamp).total_seconds() / 3600.0) / 72.0)
    return _clamp(math.tanh(surprise * 4.0) * polarity * (0.75 + 0.25 * importance) * freshness)

def _request_json(url: str, timeout: float, provider_label: str) -> list[dict[str, object]]:
    request = Request(url, headers={"User-Agent": "Forex-AI-Intelligence-Engine/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 429:
            raise FundamentalDataError(f"{provider_label} rate limit exceeded (HTTP 429).") from exc
        raise FundamentalDataError(f"{provider_label} request failed: HTTP {exc.code}.") from exc
    except Exception as exc:
        raise FundamentalDataError(f"{provider_label} request failed: {exc}") from exc
    if not isinstance(payload, list):
        raise FundamentalDataError(f"{provider_label} returned an invalid payload.")
    return [item for item in payload if isinstance(item, dict)]

def _fetch_country(country: str, start: datetime, end: datetime, timeout: float) -> list[dict[str, object]]:
    api_key = _secret("TRADING_ECONOMICS_API_KEY")
    if not api_key:
        raise FundamentalDataError("TRADING_ECONOMICS_API_KEY is not configured.")
    url = f"{TE_URL}/{quote(country)}/{start:%Y-%m-%d}/{end:%Y-%m-%d}?c={quote(api_key)}&f=json"
    return _request_json(url, timeout, "Trading Economics macro feed")

def _fetch_country_news(country: str, start: datetime, end: datetime, timeout: float) -> list[dict[str, object]]:
    api_key = _secret("TRADING_ECONOMICS_API_KEY")
    if not api_key:
        raise FundamentalDataError("TRADING_ECONOMICS_API_KEY is not configured.")
    url = f"{NEWS_URL}/{quote(country)}/{start:%Y-%m-%d}/{end:%Y-%m-%d}?c={quote(api_key)}&f=json"
    return _request_json(url, timeout, "Trading Economics news feed")

def _fetch_ticker_news(ticker: str, timeout: float) -> list[dict[str, object]]:
    api_key = _secret("TRADING_ECONOMICS_API_KEY")
    if not api_key:
        raise FundamentalDataError("TRADING_ECONOMICS_API_KEY is not configured.")
    url = f"{NEWS_TICKER_URL}/{quote(ticker, safe='')}?c={quote(api_key)}&f=json"
    return _request_json(url, timeout, "Trading Economics commodity news feed")

def _currency_score(events: list[dict[str, object]], now: datetime, polarity_rules: dict[str, float] = POLARITY_RULES) -> tuple[float | None, int, int, list[dict[str, object]]]:
    weighted = []
    for event in events:
        score = _event_score(event, now, polarity_rules)
        if score is None:
            continue
        importance = max(1.0, min(3.0, float(event.get("Importance") or 1)))
        stamp = _parse_datetime(event.get("Date"))
        freshness = math.exp(-max(0.0, (now - stamp).total_seconds() / 3600.0) / 72.0)
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
        weighted.append((score, importance * freshness, evidence))
    if not weighted:
        return None, 0, 0, []
    denominator = sum(weight for _, weight, _ in weighted)
    value = sum(score * weight for score, weight, _ in weighted) / denominator
    fresh = sum(
        1 for _, _, evidence in weighted
        if (now - _parse_datetime(evidence["date"])).total_seconds() <= 72 * 3600
    )
    evidence = [item[2] for item in sorted(weighted, key=lambda item: item[1], reverse=True)]
    return _clamp(value), len(weighted), fresh, evidence

def _news_item_score(item: dict[str, object], now: datetime) -> float | None:
    text = " ".join(
        str(item.get(key) or "")
        for key in ("title", "Title", "description", "Description", "category", "Category")
    ).lower()
    matches = [value for keyword, value in NEWS_POLARITY.items() if keyword in text]
    if not matches:
        return None
    polarity = sum(matches) / len(matches)
    stamp = _parse_datetime(item.get("date") or item.get("Date") or item.get("published") or item.get("Published"))
    freshness = math.exp(-max(0.0, (now - stamp).total_seconds() / 3600.0) / 48.0)
    return _clamp(polarity * freshness)

def _news_currency_score(items: list[dict[str, object]], now: datetime) -> tuple[float | None, int, list[dict[str, object]]]:
    scored = []
    for item in items:
        score = _news_item_score(item, now)
        if score is None:
            continue
        stamp = _parse_datetime(item.get("date") or item.get("Date") or item.get("published") or item.get("Published"))
        evidence = {
            "title": item.get("title") or item.get("Title"),
            "date": item.get("date") or item.get("Date") or item.get("published") or item.get("Published"),
            "source": item.get("source") or item.get("Source"),
            "url": item.get("url") or item.get("URL") or item.get("source_url") or item.get("SourceURL"),
            "score": round(score, 4),
        }
        weight = math.exp(-max(0.0, (now - stamp).total_seconds() / 3600.0) / 48.0)
        scored.append((score, weight, evidence))
    if not scored:
        return None, 0, []
    denominator = sum(weight for _, weight, _ in scored)
    value = sum(score * weight for score, weight, _ in scored) / denominator
    evidence = [item[2] for item in sorted(scored, key=lambda item: item[1], reverse=True)]
    return _clamp(value), len(scored), evidence

def fetch_live_news_score(
    instrument: str,
    *,
    lookback_days: int = 3,
    timeout: float = 10.0,
    now: datetime | None = None,
) -> tuple[float | None, str, int, tuple[dict[str, object], ...], str]:
    if instrument not in PAIR_CURRENCIES:
        return None, "UNAVAILABLE", 0, (), "Instrument has no mapped news currencies."
    current = now or datetime.now(timezone.utc)
    start = current - timedelta(days=max(1, lookback_days))
    try:
        base_items = _fetch_country_news(PAIR_CURRENCIES[instrument][0], start, current, timeout)
        quote_items = _fetch_country_news(PAIR_CURRENCIES[instrument][1], start, current, timeout)
    except FundamentalDataError as exc:
        return None, "UNAVAILABLE", 0, (), str(exc)
    base, base_count, base_evidence = _news_currency_score(base_items, current)
    quote, quote_count, quote_evidence = _news_currency_score(quote_items, current)
    if base is None and quote is None:
        return None, "DEGRADED", 0, (), "No directional validated live headlines."
    score = _clamp((base or 0.0) - (quote or 0.0))
    return score, "LIVE", base_count + quote_count, tuple(base_evidence + quote_evidence), "Live validated news score."

def fetch_fundamental_score(
    instrument: str,
    *,
    lookback_days: int = 7,
    timeout: float = 10.0,
    now: datetime | None = None,
) -> FundamentalResult:
    if instrument not in PAIR_CURRENCIES:
        return FundamentalResult(
            None, None, None, "UNAVAILABLE", "Trading Economics", 0, 0, {}, (),
            "Instrument has no mapped macro/news currency pair."
        )
    current = now or datetime.now(timezone.utc)
    start = current - timedelta(days=max(1, lookback_days))
    base_macro = quote_macro = None
    macro_score = None
    macro_count = macro_fresh = 0
    macro_evidence = []
    macro_message = ""
    try:
        base_events = _fetch_country(PAIR_CURRENCIES[instrument][0], start, current, timeout)
        quote_events = _fetch_country(PAIR_CURRENCIES[instrument][1], start, current, timeout)
        base_macro, base_count, base_fresh, base_evidence = _currency_score(base_events, current)
        quote_macro, quote_count, quote_fresh, quote_evidence = _currency_score(quote_events, current)
        macro_count = base_count + quote_count
        macro_fresh = base_fresh + quote_fresh
        macro_evidence = base_evidence + quote_evidence
        if base_macro is not None and quote_macro is not None:
            macro_score = _clamp(base_macro - quote_macro)
        else:
            macro_message = "Insufficient directional macro evidence."
    except FundamentalDataError as exc:
        macro_message = str(exc)

    news_score, news_status, news_count, news_evidence, news_message = fetch_live_news_score(
        instrument, lookback_days=min(lookback_days, 3), timeout=timeout, now=current
    )

    if macro_score is not None and news_score is not None:
        score = _clamp(0.70 * macro_score + 0.30 * news_score)
        status = "LIVE"
        message = "Live macro + validated live news intelligence."
    elif macro_score is not None:
        score = macro_score
        status = "DEGRADED"
        message = f"Macro live; news unavailable. {news_message}"
    elif news_score is not None:
        score = news_score
        status = "DEGRADED"
        message = f"News live; macro unavailable. {macro_message}"
    else:
        score = None
        status = "DEGRADED" if macro_count or news_count else "UNAVAILABLE"
        message = macro_message or news_message or "Insufficient validated macro/news evidence."

    evidence = tuple(macro_evidence + list(news_evidence))
    components = {
        "macro": macro_score if macro_score is not None else 0.0,
        "news": news_score if news_score is not None else 0.0,
        "combined": score if score is not None else 0.0,
    }
    return FundamentalResult(
        score,
        base_macro,
        quote_macro,
        status,
        "Trading Economics",
        macro_count + news_count,
        macro_fresh,
        components,
        evidence,
        message,
        macro_score=macro_score,
        news_score=news_score,
        news_status=news_status,
        news_evidence_count=news_count,
    )
