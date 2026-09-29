"""Fundamental-market information used by the dashboard.

The current repository does not yet ingest a live economic-calendar or
central-bank data feed. These definitions therefore describe the evidence
that a future fundamental adapter should collect; they are not live values.
"""
from __future__ import annotations

FUNDAMENTAL_INDICATORS = {
    "Interest Rate / Central Bank": {
        "description": "Policy-rate decisions, guidance and expected rate path.",
        "impact": "Rate differentials can change relative currency demand and funding conditions.",
        "source_status": "Not connected to a live fundamental feed",
    },
    "Inflation / CPI": {
        "description": "Consumer-price inflation and the direction of inflation pressure.",
        "impact": "Inflation can influence expectations for monetary-policy decisions.",
        "source_status": "Not connected to a live fundamental feed",
    },
    "GDP / Growth": {
        "description": "Economic output, growth momentum and revisions.",
        "impact": "Growth surprises can change expectations for the economic outlook.",
        "source_status": "Not connected to a live fundamental feed",
    },
    "Employment": {
        "description": "Employment, unemployment, wages and labor-market momentum.",
        "impact": "Labor data can affect growth and monetary-policy expectations.",
        "source_status": "Not connected to a live fundamental feed",
    },
    "Trade / Current Account": {
        "description": "Exports, imports, trade balance and external financing conditions.",
        "impact": "External-balance changes can affect currency supply and demand.",
        "source_status": "Not connected to a live fundamental feed",
    },
    "Commodities": {
        "description": "Oil, gas, metals and other commodity exposures relevant to some currencies.",
        "impact": "Commodity-price changes can affect terms of trade and commodity-linked currencies.",
        "source_status": "Not connected to a live fundamental feed",
    },
    "Risk Sentiment": {
        "description": "Broad risk-on/risk-off conditions across global markets.",
        "impact": "Changes in risk appetite can alter demand for different currency exposures.",
        "source_status": "Not connected to a live fundamental feed",
    },
    "Economic Calendar": {
        "description": "Scheduled releases, central-bank meetings and high-impact events.",
        "impact": "Event proximity can increase uncertainty, volatility and execution risk.",
        "source_status": "Not connected to a live economic-calendar feed",
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
