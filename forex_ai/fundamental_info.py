"""Fundamental-market information and evidence sources used by the dashboard.

The repository does not yet ingest a live economic-calendar/news feed. Source
links below are therefore research references, not claims about current market
conditions. News links are presented as evidence/navigation and must be
verified for publication time, relevance, and content before being used in a
decision.
"""
from __future__ import annotations

FUNDAMENTAL_INDICATORS = {
    "Interest Rate / Central Bank": {
        "description": "Policy-rate decisions, guidance and expected rate path.",
        "impact": "Rate differentials can change relative currency demand and funding conditions.",
        "source_status": "Reference sources available; live feed not connected",
    },
    "Inflation / CPI": {
        "description": "Consumer-price inflation and the direction of inflation pressure.",
        "impact": "Inflation can influence expectations for monetary-policy decisions.",
        "source_status": "Reference sources available; live feed not connected",
    },
    "GDP / Growth": {
        "description": "Economic output, growth momentum and revisions.",
        "impact": "Growth surprises can change expectations for the economic outlook.",
        "source_status": "Reference sources available; live feed not connected",
    },
    "Employment": {
        "description": "Employment, unemployment, wages and labor-market momentum.",
        "impact": "Labor data can affect growth and monetary-policy expectations.",
        "source_status": "Reference sources available; live feed not connected",
    },
    "Trade / Current Account": {
        "description": "Exports, imports, trade balance and external financing conditions.",
        "impact": "External-balance changes can affect currency supply and demand.",
        "source_status": "Reference sources available; live feed not connected",
    },
    "Commodities": {
        "description": "Oil, gas, metals and other commodity exposures relevant to some currencies.",
        "impact": "Commodity-price changes can affect terms of trade and commodity-linked currencies.",
        "source_status": "Reference sources available; live feed not connected",
    },
    "Risk Sentiment": {
        "description": "Broad risk-on/risk-off conditions across global markets.",
        "impact": "Changes in risk appetite can alter demand for different currency exposures.",
        "source_status": "Reference sources available; live feed not connected",
    },
    "Economic Calendar": {
        "description": "Scheduled releases, central-bank meetings and high-impact events.",
        "impact": "Event proximity can increase uncertainty, volatility and execution risk.",
        "source_status": "Reference sources available; live feed not connected",
    },
}

# Stable, manually curated research sources. These are intentionally not
# described as live news results.
FUNDAMENTAL_SOURCES = {
    "Federal Reserve": {
        "source_type": "official",
        "currency": "USD",
        "url": "https://www.federalreserve.gov/monetarypolicy.htm",
        "description": "US monetary-policy decisions, statements and related material.",
    },
    "European Central Bank": {
        "source_type": "official",
        "currency": "EUR",
        "url": "https://www.ecb.europa.eu/press/govcdec/mopo/html/index.en.html",
        "description": "ECB monetary-policy decisions and accounts.",
    },
    "Bank of England": {
        "source_type": "official",
        "currency": "GBP",
        "url": "https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes",
        "description": "BoE monetary-policy summary and minutes.",
    },
    "Bank of Japan": {
        "source_type": "official",
        "currency": "JPY",
        "url": "https://www.boj.or.jp/en/mopo/mpmdeci/index.htm",
        "description": "BoJ monetary-policy decisions.",
    },
    "Swiss National Bank": {
        "source_type": "official",
        "currency": "CHF",
        "url": "https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy",
        "description": "SNB monetary-policy framework and decisions.",
    },
    "Bank of Canada": {
        "source_type": "official",
        "currency": "CAD",
        "url": "https://www.bankofcanada.ca/core-functions/monetary-policy/",
        "description": "BoC monetary-policy framework and decisions.",
    },
    "Reserve Bank of Australia": {
        "source_type": "official",
        "currency": "AUD",
        "url": "https://www.rba.gov.au/monetary-policy/",
        "description": "RBA monetary-policy information and decisions.",
    },
    "Reserve Bank of New Zealand": {
        "source_type": "official",
        "currency": "NZD",
        "url": "https://www.rbnz.govt.nz/monetary-policy",
        "description": "RBNZ monetary-policy information and decisions.",
    },
    "FRED": {
        "source_type": "official",
        "currency": "MULTI",
        "url": "https://fred.stlouisfed.org/releases/calendar",
        "description": "US macroeconomic release calendar and economic data.",
    },
    "Reuters Forex News": {
        "source_type": "news",
        "currency": "MULTI",
        "url": "https://www.reuters.com/markets/currencies/",
        "description": "Forex and macroeconomic news coverage; verify article timestamp and context.",
    },
    "Forex Factory Calendar": {
        "source_type": "calendar",
        "currency": "MULTI",
        "url": "https://www.forexfactory.com/calendar",
        "description": "Economic calendar for research; verify against primary sources.",
    },
}

PAIR_FUNDAMENTAL_DRIVERS = {
    "EUR/USD": "ECB vs Fed policy expectations, Eurozone vs US inflation/growth, employment and risk sentiment.",
    "USD/JPY": "BoJ vs Fed policy expectations, Japan/US inflation and yields, growth and risk sentiment.",
    "GBP/USD": "BoE vs Fed policy expectations, UK/US inflation, employment and growth.",
    "AUD/USD": "RBA vs Fed policy expectations, Australian/US growth, commodities and China-linked demand.",
    "USD/CHF": "Fed vs SNB policy expectations, Swiss/US inflation and growth, plus safe-haven demand.",
    "USD/CAD": "Fed vs BoC policy expectations, US/Canadian growth, inflation and energy prices.",
    "NZD/USD": "RBNZ vs Fed policy expectations, New Zealand/US growth, commodities and global risk sentiment.",
    "XAU/USD": "US real-rate expectations, USD conditions, inflation expectations, central-bank demand and risk sentiment.",
    "XAG/USD": "US rate/USD conditions, inflation expectations, industrial demand and precious-metals sentiment.",
}


def fundamental_inputs_for(instrument: str) -> dict[str, str]:
    """Return the main fundamental drivers for an instrument."""
    return {
        "instrument": instrument,
        "drivers": PAIR_FUNDAMENTAL_DRIVERS.get(
            instrument, "Instrument-specific macroeconomic drivers."
        ),
        "status": "reference_only",
    }


def fundamental_sources_for(instrument: str) -> list[dict[str, str]]:
    """Return relevant official/news/calendar evidence sources for an instrument."""
    currency_map = {
        "EUR/USD": {"EUR", "USD"},
        "USD/JPY": {"USD", "JPY"},
        "GBP/USD": {"GBP", "USD"},
        "AUD/USD": {"AUD", "USD"},
        "USD/CHF": {"USD", "CHF"},
        "USD/CAD": {"USD", "CAD"},
        "NZD/USD": {"NZD", "USD"},
        "XAU/USD": {"USD", "MULTI"},
        "XAG/USD": {"USD", "MULTI"},
    }
    currencies = currency_map.get(instrument, {"MULTI"})
    sources = [
        item | {"evidence_id": name.lower().replace(" ", "_")}
        for name, item in FUNDAMENTAL_SOURCES.items()
        if item["currency"] in currencies or item["currency"] == "MULTI"
    ]
    return sources
