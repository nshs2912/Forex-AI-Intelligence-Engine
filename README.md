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


## Live market data

The dashboard supports **Live** and **Demo** market-data modes. Live mode uses the Twelve Data quote API for the selected forex or precious-metal instrument. Twelve Data documents real-time forex coverage and precious metals such as XAU/XAG. citeturn0search0

Configure the deployment secret/environment variable:

`TWELVE_DATA_API_KEY`

Do not commit the API key to source control.

When Live mode is selected, the dashboard:
- fetches the current provider quote;
- displays provider, symbol and UTC timestamp;
- displays bid/ask/spread when supplied;
- automatically refreshes at the selected interval;
- uses the live quote as the entry reference for the risk calculation.

The provider documents WebSocket streaming for lower-latency tick delivery; the current implementation intentionally starts with REST quote snapshots for deployment simplicity. citeturn0search3turn0search4

A live market-data quote is not a broker execution price. Spread, slippage, contract specifications, latency and broker constraints must still be validated before any trading decision.


## Decision-support governance

The dashboard implements a governed DSS pattern rather than an autonomous trading executor. It exposes data provenance, model status, calibrated probability status, feature parity, validation metrics and risk-control readiness. See `DSS_GOVERNANCE.md`.

The current trained models remain `trained_not_approved_for_live`. Live inference is only attempted when the selected major pair has a model artifact and the required completed daily OHLC features can be reconstructed consistently with training.

A DSS readiness status of `GOVERNED / NOT LIVE` is intentional when any production gate is incomplete. This prevents an unvalidated model from being presented as a production trading signal.
