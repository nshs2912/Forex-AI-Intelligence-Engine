"""Trading terminology used by the Forex AI Intelligence Engine."""

TRADING_GLOSSARY = {
    "Market Basics": {
        "Forex": "Foreign exchange market where currency pairs are traded.",
        "Currency Pair": "Two currencies quoted together, such as EUR/USD.",
        "Base Currency": "The first currency in a pair; the unit being priced.",
        "Quote Currency": "The second currency in a pair; it expresses the price.",
        "Bid": "Price at which the market buys the base currency from you.",
        "Ask": "Price at which the market sells the base currency to you.",
        "Spread": "Difference between the ask and bid price.",
        "Pip": "A standard small price increment used to measure FX movement.",
        "Lot": "Standardized trading quantity; broker contract sizes can differ.",
        "Leverage": "Use of broker-provided capital exposure relative to account equity.",
        "Margin": "Collateral required by a broker to maintain leveraged exposure.",
    },
    "Technical Analysis": {
        "ATR": "Average True Range; a volatility measure used here for dynamic SL distance.",
        "Support": "Price area where buying interest may slow or reject declines.",
        "Resistance": "Price area where selling interest may slow or reject advances.",
        "Trend": "Persistent directional movement in price.",
        "Range": "Market condition where price oscillates within a bounded area.",
        "Breakout": "Price movement beyond a meaningful support or resistance area.",
        "Volatility": "Degree and speed of price variation over time.",
        "Candlestick": "Price bar showing open, high, low, and close for a period.",
        "Timeframe": "Chart interval used to aggregate market prices.",
    },
    "Trade Management": {
        "Entry": "Planned price at which a trade is opened.",
        "Stop Loss (SL)": "Predefined exit level intended to limit trade loss.",
        "Take Profit (TP)": "Predefined exit level intended to capture a planned gain.",
        "Risk/Reward (R:R)": "Potential reward divided by the amount risked.",
        "Risk Distance": "Absolute price distance between entry and stop loss.",
        "Position Size": "Quantity of the instrument traded for a defined risk budget.",
        "Break-even Stop": "Stop moved to entry, optionally with a small offset.",
        "Trailing Stop": "Stop that follows favorable price movement while limiting reversal risk.",
        "R-Multiple": "Trade result expressed as a multiple of the initial risk.",
        "Slippage": "Difference between intended execution price and actual execution price.",
    },
    "Fundamental & Macro": {
        "Fundamental Analysis": "Assessment using economic, financial, and macroeconomic factors.",
        "Interest Rate": "Central-bank policy rate influencing currency valuation and funding.",
        "CPI": "Consumer Price Index; a measure of consumer price inflation.",
        "GDP": "Gross Domestic Product; broad measure of economic output.",
        "Employment Data": "Labor-market indicators that can affect monetary-policy expectations.",
        "Central Bank": "Institution responsible for monetary policy and currency-system functions.",
        "Economic Calendar": "Schedule of economic releases and central-bank events.",
    },
    "AI & Risk": {
        "ML": "Machine learning; models that learn patterns from historical data.",
        "Probability": "Model-estimated likelihood for a defined event or direction.",
        "Confidence": "A measure of separation or certainty in the model's directional output.",
        "Signal": "Structured evidence indicating a possible market direction or neutral state.",
        "Market Regime": "Current market state such as trending, ranging, high-volatility, or low-volatility.",
        "Risk Filter": "Rule or score that can reduce or block a trade under unsafe conditions.",
        "Walk-forward Validation": "Time-ordered training and testing procedure that avoids future-data leakage.",
        "Look-ahead Bias": "Invalid use of information that would not have been known at trade time.",
        "Backtest": "Historical simulation used to evaluate a strategy under defined assumptions.",
        "Drawdown": "Decline from a prior account or equity peak to a subsequent trough.",
        "Expectancy": "Average expected profit or loss per trade over repeated observations.",
        "Profit Factor": "Gross winning profit divided by gross losing loss.",
    },
}


def glossary_terms() -> list[tuple[str, str, str]]:
    """Return glossary entries as category, term, definition tuples."""
    return [
        (category, term, definition)
        for category, terms in TRADING_GLOSSARY.items()
        for term, definition in terms.items()
    ]
