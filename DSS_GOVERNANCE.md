# DSS Governance — Forex AI Intelligence Engine

## Intended purpose

Forex AI Intelligence Engine is a research and decision-support system (DSS) for structured analysis of market data, model outputs and risk-planning assumptions. It is not an autonomous execution system.

## Evidence chain

The DSS should preserve this chain:

1. **Data provenance** — provider, instrument, timestamp, timeframe and freshness.
2. **Feature provenance** — deterministic feature definitions shared between training and inference.
3. **Model provenance** — instrument-specific artifact, schema version, training period, calibration method and validation metrics.
4. **Decision provenance** — Fundamental, Technical, ML, Regime and Risk components and their weights.
5. **Risk provenance** — entry reference, stop-loss, take-profit, R:R and sizing assumptions.
6. **Human oversight** — the final user decision remains separate from the software output.

## ML validation policy

The current models use chronological train/calibration/test separation and Platt sigmoid calibration. A model is **not production-approved** merely because it can generate a probability.

Before live approval, each model requires:

- representative out-of-sample and walk-forward validation;
- leakage and look-ahead review;
- calibration assessment on unseen periods;
- stability analysis across market regimes;
- transaction-cost, spread and slippage sensitivity;
- broker contract and position-sizing verification;
- defined acceptance thresholds approved by the owner;
- monitoring and rollback criteria.

## Current governance state

The repository marks trained artifacts as 'trained_not_approved_for_live'. The dashboard therefore treats them as governed research models until the explicit live-use gate is satisfied.

The current 1D model requires completed daily OHLC bars. The live inference path excludes the current incomplete UTC daily bar to reduce train/inference distribution mismatch.

## DSS validity boundary

A DSS can be technically auditable without its model being proven profitable or universally valid. “Valid for DSS” therefore means that the system:

- does not fabricate probabilities;
- exposes data/model status;
- preserves feature parity;
- prevents an unapproved model from being presented as production-ready;
- separates evidence from interpretation;
- exposes uncertainty and validation limitations;
- keeps human decision authority.

It does **not** mean the system guarantees returns, predicts markets with certainty, or is approved by a financial regulator.

## Recommended production gate

'DATA OK' → 'FEATURES OK' → 'MODEL VALIDATED' → 'CALIBRATION OK' → 'RISK CONTROLS OK' → 'HUMAN REVIEW' → 'LIVE APPROVAL'.

Any failed gate should keep the DSS in 'GOVERNED / NOT LIVE'.
