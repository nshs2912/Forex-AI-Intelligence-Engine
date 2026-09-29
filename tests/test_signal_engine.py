from forex_ai.signal_engine import combine_signals

def test_bullish():
    result=combine_signals(0.8,0.7,0.9,regime=0.4,risk_filter=0.2)
    assert result.direction=="bullish"

def test_neutral():
    assert combine_signals(0,0,0).direction=="neutral"


def test_unavailable_fundamental_is_not_treated_as_neutral():
    result = combine_signals(None, 0.8, 0.4)
    assert result.components["fundamental"] is None
    assert result.score > 0.4
