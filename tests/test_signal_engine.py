from forex_ai.signal_engine import combine_signals

def test_bullish():
    result=combine_signals(0.8,0.7,0.9,regime=0.4,risk_filter=0.2)
    assert result.direction=="bullish"

def test_neutral():
    assert combine_signals(0,0,0).direction=="neutral"
