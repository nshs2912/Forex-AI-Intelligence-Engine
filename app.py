"""Minimal Streamlit dashboard."""
import streamlit as st
from forex_ai.risk_engine import build_trade_setup
from forex_ai.signal_engine import combine_signals

st.set_page_config(page_title="Forex AI Intelligence Engine", layout="wide")
st.title("Forex AI Intelligence Engine")
st.caption("Fundamental + Technical + ML with SL, TP and risk sizing.")
with st.sidebar:
    st.header("Trade setup")
    side=st.selectbox("Side",["Long","Short"])
    entry=st.number_input("Entry",min_value=0.000001,value=1.1000,format="%.6f")
    atr=st.number_input("ATR",min_value=0.000001,value=0.0080,format="%.6f")
    atr_multiplier=st.slider("ATR multiplier",0.5,4.0,1.5,0.1)
    rr=st.slider("Risk / Reward",1.0,5.0,2.0,0.1)
    balance=st.number_input("Account balance",min_value=1.0,value=10000.0)
    risk_pct=st.slider("Risk per trade (%)",0.1,5.0,1.0,0.1)
c1,c2,c3=st.columns(3)
with c1: fundamental=st.slider("Fundamental",-1.0,1.0,0.0,0.05)
with c2: technical=st.slider("Technical",-1.0,1.0,0.0,0.05)
with c3: ml=st.slider("ML direction",-1.0,1.0,0.0,0.05)
signal=combine_signals(fundamental,technical,ml)
setup=build_trade_setup(side,entry,atr,atr_multiplier=atr_multiplier,rr=rr,account_balance=balance,risk_pct=risk_pct)
m1,m2,m3,m4=st.columns(4)
m1.metric("Direction",signal.direction.title())
m2.metric("Confidence",f"{signal.confidence:.0%}")
m3.metric("Stop Loss",f"{setup.stop_loss:.6f}")
m4.metric("Take Profit",f"{setup.take_profit:.6f}")
st.subheader("Risk plan")
st.write({"Entry":setup.entry,"SL":setup.stop_loss,"TP":setup.take_profit,"R:R":setup.risk_reward,"Position units":round(setup.position_units,2)})
st.info("Decision-support only. Validate live market conditions, spread, slippage and broker constraints before use.")
