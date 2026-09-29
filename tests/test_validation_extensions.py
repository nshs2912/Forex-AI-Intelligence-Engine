from forex_ai.cost_validation import CostScenario, net_return, sensitivity
from forex_ai.drift_monitor import drift_status, population_stability_index
from forex_ai.walk_forward import walk_forward_validate
import numpy as np
import pandas as pd


def test_cost_sensitivity_applies_round_trip_cost():
    scenario = CostScenario(spread=0.001, slippage=0.0005, commission=0.0001)
    assert abs(net_return(0.01, scenario) - 0.0069) < 1e-12
    assert sensitivity([0.01], [scenario])


def test_drift_status_thresholds():
    assert drift_status(0.05) == "stable"
    assert drift_status(0.15) == "watch"
    assert drift_status(0.30) == "drift"


def test_psi_is_non_negative_for_same_distribution():
    rng = np.random.default_rng(42)
    values = rng.normal(size=200)
    psi = population_stability_index(values, values)
    assert psi >= 0


def test_walk_forward_rejects_bad_parameters():
    frame = pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=100, tz="UTC"),
        "open": np.arange(100, dtype=float) + 1,
        "high": np.arange(100, dtype=float) + 2,
        "low": np.arange(100, dtype=float),
        "close": np.arange(100, dtype=float) + 1,
    })
    try:
        walk_forward_validate(frame, min_train_rows=50, test_rows=10, step_rows=1)
    except ValueError:
        pass
    else:
        raise AssertionError("insufficient/invalid data should not silently pass")
