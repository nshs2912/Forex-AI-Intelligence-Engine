"""Deterministic risk-control checks for DSS approval."""
from __future__ import annotations


def validate_trade_risk(
    *,
    risk_distance: float,
    reward_distance: float,
    risk_reward: float,
    position_units: float,
    risk_pct: float,
    max_risk_pct: float = 2.0,
) -> bool:
    return all(
        [
            risk_distance > 0,
            reward_distance > 0,
            risk_reward >= 1.0,
            position_units > 0,
            0 < risk_pct <= max_risk_pct,
        ]
    )
