from forex_ai.glossary import TRADING_GLOSSARY, glossary_terms


def test_glossary_has_core_trading_terms():
    terms = {term for _, term, _ in glossary_terms()}
    assert {"ATR", "Stop Loss (SL)", "Take Profit (TP)", "Risk/Reward (R:R)"} <= terms


def test_glossary_definitions_are_non_empty():
    assert glossary_terms()
    assert all(category and term and definition for category, term, definition in glossary_terms())
    assert len(TRADING_GLOSSARY) >= 4
