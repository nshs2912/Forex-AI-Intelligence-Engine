from forex_ai.ml import probability_to_direction, confidence_from_probabilities

def test_direction():
    assert probability_to_direction(0.8,0.1)>0 and probability_to_direction(0.1,0.8)<0

def test_neutral_band():
    assert probability_to_direction(0.52,0.48,neutral_band=0.1)==0

def test_confidence():
    assert confidence_from_probabilities(0.8,0.1)==0.7
