"""Streamlit dashboard for the Forex AI Intelligence Engine."""
import streamlit as st

from forex_ai.glossary import MAJOR_PAIRS, PRECIOUS_METALS, TRADING_GLOSSARY
from forex_ai.risk_engine import build_trade_setup
from forex_ai.signal_engine import combine_signals

st.set_page_config(page_title="Forex AI Intelligence Engine", layout="wide")
st.title("Forex AI Intelligence Engine")
st.caption("Fundamental + Technical + ML with instrument-aware SL, TP and risk sizing.")

INSTRUMENTS = list(MAJOR_PAIRS) + list(PRECIOUS_METALS)

with st.sidebar:
    st.header("Trade setup")
    instrument = st.selectbox("Instrument", INSTRUMENTS, index=0)
    asset_class = "Forex" if instrument in MAJOR_PAIRS else "Precious Metal"
    st.caption(f"Asset class: {asset_class}")

    side = st.selectbox("Side", ["Long", "Short"])
    entry = st.number_input("Entry", min_value=0.000001, value=1.1000, format="%.6f")
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
        st.caption("Full glossary: TRADING_GLOSSARY.md")

pair_description = MAJOR_PAIRS.get(instrument) or PRECIOUS_METALS[instrument]
st.subheader(f"📊 {instrument}")
st.info(pair_description)

m0, m1, m2, m3, m4 = st.columns(5)
m0.metric("Asset Class", asset_class)
m1.metric("Direction", "Pending")
m2.metric("Stop Loss", "—")
m3.metric("Take Profit", "—")
m4.metric("R:R", f"{rr:.1f}")

c1, c2, c3 = st.columns(3)
with c1:
    fundamental = st.slider("Fundamental", -1.0, 1.0, 0.0, 0.05)
with c2:
    technical = st.slider("Technical", -1.0, 1.0, 0.0, 0.05)
with c3:
    ml = st.slider("ML direction", -1.0, 1.0, 0.0, 0.05)

signal = combine_signals(fundamental, technical, ml)
setup = build_trade_setup(
    side, entry, atr, atr_multiplier=atr_multiplier, rr=rr,
    account_balance=balance, risk_pct=risk_pct,
)

m1.metric("Direction", signal.direction.title())
m1.caption(f"Confidence {signal.confidence:.0%}")
m2.metric("Stop Loss", f"{setup.stop_loss:.6f}")
m3.metric("Take Profit", f"{setup.take_profit:.6f}")
m4.metric("R:R", f"{setup.risk_reward:.2f}")

st.subheader("Risk plan")
st.write({
    "Instrument": instrument,
    "Asset class": asset_class,
    "Entry": setup.entry,
    "SL": setup.stop_loss,
    "TP": setup.take_profit,
    "R:R": setup.risk_reward,
    "Position units": round(setup.position_units, 2),
})
st.info(
    "Decision-support only. Validate live market conditions, spread, slippage, "
    "contract specifications and broker constraints before use."
)
