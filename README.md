# Forex AI Intelligence Engine

AI-assisted forex research and risk-management engine.

## Layers
- Fundamental analysis inputs
- Technical analysis inputs
- ML directional probabilities
- Explainable ensemble scoring
- Market-regime and risk filters
- Dynamic ATR + support/resistance SL
- Dynamic TP with configurable risk/reward
- Position sizing by account risk
- Break-even and trailing-stop calculations
- Automated unit tests and GitHub Actions CI

## Risk design
SL and TP are planning outputs, not execution commands. The engine uses ATR and optional support/resistance levels. Live implementations should additionally apply spread, slippage, liquidity, broker stop-distance, session and economic-news filters.

## ML design
The repository provides model contracts rather than claiming a trained model is profitable. Production ML should use time-ordered/walk-forward validation and prevent look-ahead leakage.

> Decision-support software only; not financial advice or a guarantee of returns.
