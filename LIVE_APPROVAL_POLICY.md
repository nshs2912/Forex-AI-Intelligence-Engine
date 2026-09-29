# Live Approval Policy

## Purpose

This policy defines how a Forex AI model may progress from research to live
decision-support use. A green software build is not equivalent to model
approval.

## Status lifecycle

`trained_not_approved_for_live` → `validated_for_paper` →
`candidate_for_live` → `approved_for_live` → `revoked`

A model may move forward only when the evidence for the previous stage exists.

## Mandatory live gates

1. Data integrity and provenance.
2. Shared training/inference feature parity.
3. Chronological out-of-sample evaluation.
4. Walk-forward evaluation.
5. Probability calibration on unseen data.
6. Leakage/look-ahead audit.
7. Performance acceptance thresholds.
8. Market-regime stability.
9. Spread, slippage and transaction-cost sensitivity.
10. Broker-specific contract and position-sizing validation.
11. Risk limits, maximum-loss controls and kill-switch behavior.
12. Operational monitoring and rollback.
13. Model/version registry.
14. Human approval recorded in an immutable audit record.

The repository's automated artifact gate currently requires at minimum:
- test rows >= 250;
- ROC-AUC >= 0.55;
- Brier score <= 0.25;
- PR-AUC >= the test positive-rate baseline;
- model data ending no more than 365 days before validation;
- expected schema, calibration and feature parity.

These thresholds are software acceptance criteria, not guarantees of profitability.

## Non-negotiable rule

CI must never change a model to `approved_for_live` merely because training
completed. The approval record must exist separately and the automated
validation must pass.

## Current state

The current repository models use historical data ending in 2023. Therefore
they cannot be approved for live use in 2026 until the training dataset is
refreshed and the resulting model passes the full validation process.

## Paper trading

Before live approval, the system should operate in paper mode with the same
feature, signal and risk paths intended for live use. Paper results are
evidence for operational validation, not a guarantee of future performance.

## Revocation

Approval must be revoked when validation gates fail, material drift is
detected, the model or feature schema changes without re-validation, a data
provider becomes unreliable, or a defined risk/incident threshold is breached.
