"""Streamlit dashboard for the Forex AI Intelligence Engine."""
import streamlit as st
import streamlit.components.v1 as components
from datetime import timezone
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh

from forex_ai.glossary import MAJOR_PAIRS, PRECIOUS_METALS, TRADING_GLOSSARY
from forex_ai.market_data import MarketDataError, fetch_live_quote
from forex_ai.probability import unavailable_result
from forex_ai.risk_engine import build_trade_setup
from forex_ai.signal_engine import combine_signals

st.set_page_config(page_title="Forex AI Intelligence Engine", layout="wide")
st.title("Forex AI Intelligence Engine")
st.caption("Live market data + Fundamental + Technical + ML with instrument-aware SL, TP and risk sizing.")

INSTRUMENTS = list(MAJOR_PAIRS) + list(PRECIOUS_METALS)

with st.sidebar:
    st.header("Trade setup")
    data_mode = st.radio("Market data", ["Live", "Demo"], horizontal=True)
    timezone_options = {
        "WIB (UTC+7)": "Asia/Jakarta",
        "WITA (UTC+8)": "Asia/Makassar",
        "WIT (UTC+9)": "Asia/Jayapura",
    }
    display_timezone = st.selectbox("Zona waktu", list(timezone_options), index=0)
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
            f"{live_quote.price:.6f} | {display_timezone} "
            f"{live_quote.received_at.astimezone(ZoneInfo(timezone_options[display_timezone])):%d-%m-%Y %I:%M:%S %p}"
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

st.subheader("🧭 Signal inputs")
st.caption(
    "Skala sinyal: +1 = bullish kuat, 0 = netral, −1 = bearish kuat. "
    "Nilai di antaranya menunjukkan kekuatan arah; angka tidak berarti probabilitas."
)
c1, c2, c3 = st.columns(3)
with c1:
    fundamental = st.slider("Fundamental", -1.0, 1.0, 0.0, 0.05)
    st.caption("−1 bearish kuat · 0 netral · +1 bullish kuat")
with c2:
    technical = st.slider("Technical", -1.0, 1.0, 0.0, 0.05)
    st.caption("−1 bearish kuat · 0 netral · +1 bullish kuat")
with c3:
    ml = st.slider("ML Direction", -1.0, 1.0, 0.0, 0.05)
    st.caption("−1 bearish kuat · 0 netral · +1 bullish kuat")

signal = combine_signals(fundamental, technical, ml)

# Do not convert the ensemble score into a fake probability.
# A probability is shown only when a separately trained/calibrated model is supplied.
probability = unavailable_result()
if signal.direction == "bullish":
    trade_action = "BUY"
elif signal.direction == "bearish":
    trade_action = "SELL"
else:
    trade_action = "WAIT"

setup = build_trade_setup(
    side,
    entry,
    atr,
    atr_multiplier=atr_multiplier,
    rr=rr,
    account_balance=balance,
    risk_pct=risk_pct,
)

st.subheader("🎯 AI Market Signal")
a0, a1, a2, a3 = st.columns(4)
a0.metric("Position", trade_action)
a1.metric("Reference Price", f"{entry:.6f}")
a2.metric("Bullish", "N/A")
a3.metric("Bearish", "N/A")
st.caption(
    "Calibrated probability: not available. The current engine exposes a directional score; "
    "a held-out calibration model is required before displaying a true probability."
)

m0, m1, m2, m3, m4 = st.columns(5)
m0.metric("Asset Class", asset_class)
m1.metric("Direction", signal.direction.title())
m2.metric("Stop Loss", f"{setup.stop_loss:.6f}")
m3.metric("Take Profit", f"{setup.take_profit:.6f}")
m4.metric("R:R", f"{setup.risk_reward:.2f}")
st.caption(
    f"Signal confidence: {signal.confidence:.0%} · "
    f"Probability status: {probability.status}"
)

st.subheader("🛡️ Risk Plan")
st.caption("Ringkasan level perdagangan yang dihitung oleh Risk Engine.")

r1, r2, r3, r4 = st.columns(4)
r1.metric("Position", trade_action)
r2.metric("Instrument", instrument)
r3.metric("Entry Price", f"{setup.entry:.6f}")
r4.metric("R:R", f"1 : {setup.risk_reward:.2f}")

r5, r6, r7, r8 = st.columns(4)
r5.metric("Reference Price", f"{entry:.6f}")
r6.metric("Stop Loss", f"{setup.stop_loss:.6f}")
r7.metric("Take Profit", f"{setup.take_profit:.6f}")
r8.metric("Position Units", f"{setup.position_units:,.2f}")

st.caption(
    f"Asset class: {asset_class} · Data mode: {data_mode} · "
    f"Risk per trade: {risk_pct:.1f}%"
)

if data_mode == "Live" and live_quote:
    received_ms = live_quote.received_at.timestamp() * 1000
    tz_name = timezone_options[display_timezone]
    components.html(
        f"""
        <div style="font-family: sans-serif; padding: 4px 0;">
          <div id="clock" style="font-size: 1.05rem; font-weight: 600;"></div>
          <div style="font-size: 0.82rem; color: #666;">
            Jam berjalan • {display_timezone} • data diterima dashboard
          </div>
        </div>
        <script>
          const tz = {tz_name!r};
          function tick() {{
            const now = new Date();
            const parts = new Intl.DateTimeFormat("en-GB", {{
              timeZone: tz,
              day: "2-digit", month: "2-digit", year: "numeric",
              hour: "2-digit", minute: "2-digit", second: "2-digit",
              hour12: true
            }}).formatToParts(now);
            const get = (name) => parts.find(p => p.type === name)?.value || "";
            document.getElementById("clock").textContent =
              get("day") + "-" + get("month") + "-" + get("year") + " " +
              get("hour") + ":" + get("minute") + ":" + get("second") + " " +
              get("dayPeriod") + " {display_timezone}";
          }}
          tick();
          setInterval(tick, 1000);
        </script>
        """,
        height=58,
    )
    st.caption(f"Automatic market-data refresh: every {refresh} seconds. The clock above runs continuously between refreshes.")

st.info(
    "Decision-support only. Live quotes are market-data snapshots, not execution prices. "
    "Validate spread, slippage, contract specifications and broker constraints before use."
)
