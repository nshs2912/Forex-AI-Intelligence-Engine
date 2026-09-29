"""Risk and trade-setup calculations for forex research."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TradeSetup:
    side: str
    entry: float
    stop_loss: float
    take_profit: float
    risk_distance: float
    reward_distance: float
    risk_reward: float
    position_units: float

def calculate_levels(side: str, entry: float, atr: float, *, atr_multiplier: float=1.5, rr: float=2.0):
    side=side.strip().lower()
    if side not in {"long","short"}: raise ValueError("side must be 'long' or 'short'")
    if entry<=0 or atr<=0: raise ValueError("entry and atr must be positive")
    if atr_multiplier<=0 or rr<=0: raise ValueError("atr_multiplier and rr must be positive")
    risk=atr*atr_multiplier; reward=risk*rr
    sl,tp=(entry-risk,entry+reward) if side=="long" else (entry+risk,entry-reward)
    if sl<=0 or tp<=0: raise ValueError("calculated price levels must be positive")
    return sl,tp,risk,reward

def calculate_position_size(account_balance: float, risk_pct: float, risk_distance: float, *, pip_size: float, pip_value_per_unit: float):
    if account_balance<=0 or risk_distance<=0 or pip_size<=0 or pip_value_per_unit<=0: raise ValueError("inputs must be positive")
    if not 0<risk_pct<=100: raise ValueError("risk_pct must be in (0, 100]")
    risk_cash=account_balance*risk_pct/100.0
    risk_pips=risk_distance/pip_size
    return risk_cash/(risk_pips*pip_value_per_unit)

def build_trade_setup(side: str, entry: float, atr: float, *, atr_multiplier: float=1.5, rr: float=2.0, account_balance: float=10000.0, risk_pct: float=1.0, pip_size: float=0.0001, pip_value_per_unit: float=0.00001):
    sl,tp,risk,reward=calculate_levels(side,entry,atr,atr_multiplier=atr_multiplier,rr=rr)
    units=calculate_position_size(account_balance,risk_pct,risk,pip_size=pip_size,pip_value_per_unit=pip_value_per_unit)
    return TradeSetup(side.strip().lower(),entry,sl,tp,risk,reward,rr,units)
