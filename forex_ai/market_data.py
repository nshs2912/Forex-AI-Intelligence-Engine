"""Live market-data adapter for the Forex AI Intelligence Engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os

try:
    import streamlit as st
except ImportError:  # pragma: no cover - library remains usable outside Streamlit
    st = None
from urllib.parse import quote
from urllib.request import Request, urlopen
import json

import pandas as pd


TWELVE_DATA_URL = "https://api.twelvedata.com/quote"
TWELVE_DATA_TIME_SERIES_URL = "https://api.twelvedata.com/time_series"


@dataclass(frozen=True)
class MarketQuote:
    symbol: str
    price: float
    bid: float | None
    ask: float | None
    timestamp: datetime
    source: str
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MarketDataError(RuntimeError):
    """Raised when live market data cannot be retrieved."""


def quote_age_seconds(
    quote: MarketQuote, *, now: datetime | None = None
) -> float:
    """Return provider-quote age in seconds, clamped at zero."""
    reference = now or datetime.now(timezone.utc)
    timestamp = quote.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    age = (reference - timestamp.astimezone(timezone.utc)).total_seconds()
    return max(0.0, age)


def quote_freshness(age_seconds: float) -> str:
    """Classify a quote snapshot for dashboard observability."""
    if age_seconds <= 60:
        return "FRESH"
    if age_seconds <= 300:
        return "AGING"
    return "STALE"


def _api_key() -> str:
    key = ""
    if st is not None:
        try:
            key = str(st.secrets.get("TWELVE_DATA_API_KEY", "")).strip()
        except Exception:
            key = ""
    if not key:
        key = os.getenv("TWELVE_DATA_API_KEY", "").strip()
    if not key:
        raise MarketDataError(
            "TWELVE_DATA_API_KEY is not configured. Add it to Streamlit Secrets "
            "or the deployment environment."
        )
    return key


def fetch_live_quote(symbol: str, timeout: float = 10.0) -> MarketQuote:
    """Fetch the latest quote from Twelve Data.

    The provider returns a current quote snapshot. The timestamp is the
    provider timestamp when available, normalized to UTC.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("symbol must not be empty")

    key = _api_key()
    url = f"{TWELVE_DATA_URL}?symbol={quote(symbol)}&apikey={quote(key)}"
    request = Request(url, headers={"User-Agent": "Forex-AI-Intelligence-Engine/1.0"})

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise MarketDataError(f"Live market-data request failed: {exc}") from exc

    if payload.get("status") == "error" or payload.get("code"):
        raise MarketDataError(payload.get("message", "Provider returned an error"))

    try:
        price = float(payload["close"])
    except (KeyError, TypeError, ValueError) as exc:
        raise MarketDataError("Provider response does not contain a valid price") from exc

    timestamp = _parse_timestamp(payload.get("datetime"), payload.get("timestamp"))
    bid = _optional_float(payload.get("bid"))
    ask = _optional_float(payload.get("ask"))

    return MarketQuote(
        symbol=symbol,
        price=price,
        bid=bid,
        ask=ask,
        timestamp=timestamp,
        received_at=datetime.now(timezone.utc),
        source="Twelve Data",
    )

def fetch_daily_history(
    symbol: str, *, outputsize: int = 60, timeout: float = 15.0
) -> pd.DataFrame:
    """Fetch daily OHLC history used by the 1D ML feature pipeline."""
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("symbol must not be empty")
    if outputsize < 30:
        raise ValueError("outputsize must be at least 30 for the feature pipeline")
    key = _api_key()
    url = (
        f"{TWELVE_DATA_TIME_SERIES_URL}?symbol={quote(symbol)}"
        f"&interval=1day&outputsize={outputsize}&apikey={quote(key)}"
    )
    request = Request(
        url, headers={"User-Agent": "Forex-AI-Intelligence-Engine/1.0"}
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise MarketDataError(f"Historical market-data request failed: {exc}") from exc
    if payload.get("status") == "error" or payload.get("code"):
        raise MarketDataError(payload.get("message", "Provider returned an error"))
    values = payload.get("values")
    if not isinstance(values, list) or not values:
        raise MarketDataError("Provider returned no historical values")
    frame = pd.DataFrame(values)
    required = {"datetime", "open", "high", "low", "close"}
    missing = required.difference(frame.columns)
    if missing:
        raise MarketDataError(f"Historical response missing columns: {sorted(missing)}")
    frame = frame.rename(columns={"datetime": "date"})
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    for column in ["open", "high", "low", "close", "volume", "tick_volume"]:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if "tick_volume" not in frame.columns:
        frame["tick_volume"] = frame.get("volume", 0.0)
    frame = frame.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    return frame.dropna(subset=["open", "high", "low", "close"]).copy()


def _optional_float(value) -> float | None:
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_timestamp(value, unix_timestamp=None) -> datetime:
    if unix_timestamp not in (None, ""):
        try:
            return datetime.fromtimestamp(float(unix_timestamp), tz=timezone.utc)
        except (TypeError, ValueError, OverflowError):
            pass
    if value:
        text = str(value).replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)
