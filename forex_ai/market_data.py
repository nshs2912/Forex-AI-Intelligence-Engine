"""Live market-data adapter for the Forex AI Intelligence Engine."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os

try:
    import streamlit as st
except ImportError:  # pragma: no cover - library remains usable outside Streamlit
    st = None
from urllib.parse import quote
from urllib.request import Request, urlopen
import json


TWELVE_DATA_URL = "https://api.twelvedata.com/quote"


@dataclass(frozen=True)
class MarketQuote:
    symbol: str
    price: float
    bid: float | None
    ask: float | None
    timestamp: datetime
    source: str


class MarketDataError(RuntimeError):
    """Raised when live market data cannot be retrieved."""


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
        source="Twelve Data",
    )


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
