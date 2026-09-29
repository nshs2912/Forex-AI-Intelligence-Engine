from forex_ai.risk_engine import calculate_levels, calculate_position_size, breakeven_stop, trailing_stop

def test_sr_aware_long():
    sl,tp,risk,reward,rr=calculate_levels("long",1.1,.01,atr_multiplier=1.5,rr=2,support=1.09)
    assert sl<1.1 and risk>0 and rr>0

def test_position_size():
    assert calculate_position_size(10000,1,.01,pip_size=.0001,pip_value_per_unit=.00001)==100000

def test_breakeven():
    assert breakeven_stop("long",1.1,1.12,risk_distance=.01)==1.1
    assert breakeven_stop("long",1.1,1.105,risk_distance=.01) is None

def test_trailing_stop_never_moves_against_long():
    first=trailing_stop("long",1.12,.01,atr_multiplier=1)
    second=trailing_stop("long",1.115,.01,atr_multiplier=1,previous_stop=first)
    assert second==first
