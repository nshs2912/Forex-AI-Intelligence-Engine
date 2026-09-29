from forex_ai.risk_engine import calculate_levels, calculate_position_size

def test_long_levels():
    sl,tp,risk,reward,actual_rr=calculate_levels("long",1.1000,0.0100,atr_multiplier=1.5,rr=2.0)
    assert round(sl,6)==1.085 and round(tp,6)==1.13 and round(risk,6)==0.015 and round(reward,6)==0.03 and round(actual_rr,6)==2.0

def test_short_levels():
    sl,tp,_,_,actual_rr=calculate_levels("short",150.0,1.0,atr_multiplier=1.0,rr=2.0)
    assert sl==151.0 and tp==148.0 and actual_rr==2.0

def test_position_size():
    assert calculate_position_size(10000,1.0,0.01,pip_size=0.0001,pip_value_per_unit=0.00001)==1000.0
