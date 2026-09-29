"""Streamlit dashboard for the Forex AI Intelligence Engine."""
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from forex_ai.glossary import MAJOR_PAIRS, PRECIOUS_METALS, TRADING_GLOSSARY
from forex_ai.market_data import MarketDataError, fetch_live_quote
from forex_ai.risk_engine import build_trade_setup
from forex_ai.signal_engine import combine_signals

st.set_page_config(page_title="Forex AI Intelligence Engine", layout="wide")
st.title("Forex AI Intelligence Engine")
st.caption("Live market data + Fundamental + Technical + ML with instrument-aware SL, TP and risk sizing.")

INSTRUMENTS = list(MAJOR_PAIRS) + list(PRECIOUS_METALS)

with st.sidebar:
    st.header("Trade setup")
    data_mode = st.radio("Market data", ["Live", "Demo"], horizontal=True)
    instrument = st.selectbox("Instrument", INSTRUMENTS, index=0)
    asset_class = "Forex" if instrument in MAJOR_PAIRS else "Precious Metal"

    if data_mode == "Live":
        refresh = st.slider("Refresh interval (seconds)", 15, 300, 30, 15)
        st_autorefresh(interval=refresh * 1000, key="market_refresh")
        st.caption("Live mode requires the TWELVE_DATA_API_KEY secret.")
    else:
        refresh = 0

    side = st.selectbox("Side", ["Long", "Short"])
    entry = st.number_input("Demo Entry", min_value=0.000001, value=1.1000, format="%.6f")
    atr = st.number_input("ATR", min_value=0.000001, value=0.0080, format="%.6f")
    atr_multiplier = st.slider("ATR multiplier", 0.5, 4.0, 1.5, 0.1)
    rr = st.slider("Risk / Reward", 1.0, 5.0, 2.0, 0.1)
    balance = st.number_input("Account balance", min_value=1.0, value=10000.0)
    risk_pct = st.slider("Risk per trade (%)", 0.1, 5.0, 1.0, 0.1)

    st.divider()
    with st.expander("📖 Trading Glossary", expanded=False):
        category = st.selectbox("Category", list(TRADING_GLOSSARY))
        terms = TRADING_GLOSSARY[category]
        term = st.selectbox("Term", list(terms))
        st.markdown(f"**{term}**")
        st.write(terms[term])

pair_description = MAJOR_PAIRS.get(instrument) or PRECIOUS_METALS[instrument]
st.subheader(f"📊 {instrument}")
st.info(pair_description)

live_quote = None
if data_mode == "Live":
    try:
        live_quote = fetch_live_quote(instrument)
        entry = live_quote.price
        st.success(
            f"📡 LIVE — {live_quote.source} | {live_quote.symbol} | "
            f"{live_quote.price:.6f} | UTC {live_quote.timestamp:%Y-%m-%d %H:%M:%S}"
        )
        if live_quote.bid is not None and live_quote.ask is not None:
            st.caption(
                f"Bid: {live_quote.bid:.6f} · Ask: {live_quote.ask:.6f} · "
                f"Spread: {live_quote.ask - live_quote.bid:.6f}"
            )
    except MarketDataError as exc:
        st.error(f"Live market data unavailable: {exc}")
        st.warning("Switch to Demo mode or configure TWELVE_DATA_API_KEY.")

with st.expander("📋 Supported instruments", expanded=False):
    st.markdown("**7 Major Currency Pairs**")
    st.write(", ".join(MAJOR_PAIRS))
    st.markdown("**Precious Metals**")
    st.write(", ".join(PRECIOUS_METALS))

c1, c2, c3 = st.columns(3)
with c1:
    fundamental = st.slider("Fundamental", -1.0, 1.0, 0.0, 0.05)
with c2:
    technical = st.slider("Technical", -1.0, 1.0, 0.0, 0.05)
with c3:
    ml = st.slider("ML direction", -1.0, 1.0, 0.0, 0.05)

signal = combine_signals(fundamental, technical, ml)
setup = build_trade_setup(
    side,
    entry,
    atr,
    atr_multiplier=atr_multiplier,
    rr=rr,
    account_balance=balance,
    risk_pct=risk_pct,
)

m0, m1, m2, m3, m4 = st.columns(5)
m0.metric("Asset Class", asset_class)
m1.metric("Direction", signal.direction.title())
m2.metric("Stop Loss", f"{setup.stop_loss:.6f}")
m3.metric("Take Profit", f"{setup.take_profit:.6f}")
m4.metric("R:R", f"{setup.risk_reward:.2f}")
st.caption(f"Signal confidence: {signal.confidence:.0%}")

st.subheader("Risk plan")
st.write(
    {
        "Data mode": data_mode,
        "Instrument": instrument,
        "Asset class": asset_class,
        "Entry": setup.entry,
        "SL": setup.stop_loss,
        "TP": setup.take_profit,
        "R:R": setup.risk_reward,
        "Position units": round(setup.position_units, 2),
    }
)

if data_mode == "Live":
    st.caption(f"Automatic refresh: every {refresh} seconds.")

st.info(
    "Decision-support only. Live quotes are market-data snapshots, not execution prices. "
    "Validate spread, slippage, contract specifications and broker constraints before use."
)
