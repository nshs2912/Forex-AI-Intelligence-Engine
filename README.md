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
- Trading glossary in documentation and dashboard
- Automated unit tests and GitHub Actions CI

## Risk design
SL and TP are planning outputs, not execution commands. The engine uses ATR and optional support/resistance levels. Live implementations should additionally apply spread, slippage, liquidity, broker stop-distance, session and economic-news filters.

## ML design
The repository provides model contracts rather than claiming a trained model is profitable. Production ML should use time-ordered/walk-forward validation and prevent look-ahead leakage.

## Trading glossary
See TRADING_GLOSSARY.md for terminology covering:
- Forex market basics
- Technical analysis
- Entry, SL, TP, R:R and position sizing
- Fundamental and macro concepts
- ML, backtesting and risk concepts

The Streamlit dashboard also includes a compact glossary selector in the sidebar.

## CI reliability
The repository explicitly configures pytest to include the project root in its Python path and runs compilation plus python -m pytest -q in GitHub Actions.

> Decision-support software only; not financial advice or a guarantee of returns.
