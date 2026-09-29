from forex_ai.glossary import MAJOR_PAIRS, PRECIOUS_METALS, TRADING_GLOSSARY, glossary_terms


def test_glossary_has_core_trading_terms():
    terms = {term for _, term, _ in glossary_terms()}
    assert {"ATR", "Stop Loss (SL)", "Take Profit (TP)", "Risk/Reward (R:R)"} <= terms


def test_glossary_definitions_are_non_empty():
    assert glossary_terms()
    assert all(category and term and definition for category, term, definition in glossary_terms())
    assert len(TRADING_GLOSSARY) >= 4


def test_core_major_pairs_and_metals():
    assert len(MAJOR_PAIRS) == 7
    assert {"EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CHF", "USD/CAD", "NZD/USD"} == set(MAJOR_PAIRS)
    assert "XAU/USD" in PRECIOUS_METALS
    assert "XAG/USD" in PRECIOUS_METALS
