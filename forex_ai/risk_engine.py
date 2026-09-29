"""Dynamic risk engine for forex trade planning."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TradeSetup:
    side: str; entry: float; stop_loss: float; take_profit: float; risk_distance: float; reward_distance: float; risk_reward: float; position_units: float

def _positive(**values):
    if any(value <= 0 for value in values.values()):
        raise ValueError("numeric inputs must be positive")

def calculate_levels(side, entry, atr, *, atr_multiplier=1.5, rr=2.0, support=None, resistance=None, buffer_atr=0.10):
    side = side.strip().lower()
    if side not in {"long", "short"}:
        raise ValueError("side must be long or short")
    _positive(entry=entry, atr=atr, atr_multiplier=atr_multiplier, rr=rr)
    if buffer_atr < 0:
        raise ValueError("buffer_atr must be non-negative")
    distance = atr * atr_multiplier
    if side == "long":
        sl = entry - distance
        if support is not None:
            sl = min(sl, support - atr * buffer_atr)
        risk = entry - sl
        tp = entry + risk * rr
        if resistance is not None:
            tp = min(tp, resistance - atr * buffer_atr)
    else:
        sl = entry + distance
        if resistance is not None:
            sl = max(sl, resistance + atr * buffer_atr)
        risk = sl - entry
        tp = entry - risk * rr
        if support is not None:
            tp = max(tp, support + atr * buffer_atr)
    if sl <= 0 or tp <= 0 or risk <= 0:
        raise ValueError("invalid price levels")
    reward = abs(tp - entry)
    return sl, tp, risk, reward, reward / risk

def calculate_position_size(account_balance, risk_pct, risk_distance, *, pip_size, pip_value_per_unit):
    """Return units sized so the stop distance consumes the risk budget."""
    _positive(account_balance=account_balance, risk_distance=risk_distance, pip_size=pip_size, pip_value_per_unit=pip_value_per_unit)
    if not 0 < risk_pct <= 100:
        raise ValueError("risk_pct must be in (0,100]")
    risk_budget = account_balance * risk_pct / 100
    loss_per_unit = risk_distance / pip_size * pip_value_per_unit
    return risk_budget / loss_per_unit

def build_trade_setup(side, entry, atr, *, atr_multiplier=1.5, rr=2.0, account_balance=10000, risk_pct=1.0, pip_size=.0001, pip_value_per_unit=.00001, support=None, resistance=None):
    sl, tp, risk, reward, actual_rr = calculate_levels(side, entry, atr, atr_multiplier=atr_multiplier, rr=rr, support=support, resistance=resistance)
    units = calculate_position_size(account_balance, risk_pct, risk, pip_size=pip_size, pip_value_per_unit=pip_value_per_unit)
    return TradeSetup(side.lower(), entry, sl, tp, risk, reward, actual_rr, units)

def breakeven_stop(side, entry, current_price, *, risk_distance, trigger_r=1.0, offset=0.0):
    _positive(risk_distance=risk_distance, trigger_r=trigger_r)
    side = side.lower()
    triggered = ((current_price - entry) >= risk_distance * trigger_r if side == "long" else (entry - current_price) >= risk_distance * trigger_r)
    return (entry + offset if side == "long" else entry - offset) if triggered else None

def trailing_stop(side, current_price, atr, *, atr_multiplier=1.5, previous_stop=None):
    _positive(current_price=current_price, atr=atr, atr_multiplier=atr_multiplier)
    side = side.lower()
    candidate = current_price - atr * atr_multiplier if side == "long" else current_price + atr * atr_multiplier
    if previous_stop is None:
        return candidate
    return max(previous_stop, candidate) if side == "long" else min(previous_stop, candidate)
