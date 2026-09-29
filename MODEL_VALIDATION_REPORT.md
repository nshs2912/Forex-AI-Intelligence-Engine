# Model Validation Report — Current Baseline

**Assessment date:** 2026-09-29  
**System:** Forex AI Intelligence Engine  
**Decision:** NOT APPROVED FOR LIVE

## Evidence

The current artifacts were trained on a public historical dataset whose available
range ends on 2023-01-10. The repository therefore fails the live-recency gate
for a 2026 deployment.

The latest recorded test metrics are:

| Pair | ROC-AUC | PR-AUC | Brier | Test rows |
|---|---:|---:|---:|---:|
| EUR/USD | 0.542 | 0.509 | 0.255 | 312 |
| GBP/USD | 0.455 | 0.430 | 0.267 | 331 |
| USD/JPY | 0.449 | 0.564 | 0.273 | 335 |
| AUD/USD | 0.488 | 0.480 | 0.260 | 370 |
| USD/CHF | 0.562 | 0.582 | 0.255 | 333 |
| USD/CAD | 0.479 | 0.474 | 0.251 | 305 |
| NZD/USD | 0.444 | 0.415 | 0.252 | 373 |

## Blocking findings

1. **Data freshness fails.** Historical training data ends in 2023, while the
   intended deployment context is 2026.
2. **Performance acceptance is not met consistently.** Several models have
   ROC-AUC below 0.50 and all recorded Brier scores are above the repository's
   current live gate of 0.25.
3. **No completed walk-forward evidence is registered.**
4. **No transaction-cost/slippage stress report is registered.**
5. **No broker-specific contract sizing validation is registered.**
6. **No independent human approval record exists.**

## Required path to approval

1. Refresh the training data using the same market-data family intended for
   inference, preferably the configured Twelve Data source. Twelve Data
   documents daily historical OHLC data and a maximum of 5,000 records per
   request. citeturn5search0turn5search1
2. Retrain all seven major-pair models.
3. Re-run chronological out-of-sample and walk-forward validation.
4. Re-run calibration evaluation.
5. Run regime, spread, slippage and transaction-cost sensitivity tests.
6. Validate broker-specific position sizing and risk limits.
7. Run paper trading using the exact live inference path.
8. Record an explicit human approval decision and expiry/review date.
9. Only then change the model registry to `approved_for_live`.

## Governance rule

A green CI build means the software is internally consistent. It does not
mean the model is profitable or approved for live trading. The repository
therefore keeps the DSS action at **GOVERNED / NOT LIVE** until the evidence
above is complete.

NIST's AI RMF calls for pre-deployment testing, documented validity/reliability,
ongoing monitoring, incident handling, and clear governance throughout the AI
lifecycle. citeturn0search0turn0search2
