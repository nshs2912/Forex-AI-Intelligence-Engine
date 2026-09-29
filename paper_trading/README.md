# Paper Trading Evidence

Paper trading is required before live approval.

The paper environment must use the same:
- market-data adapter;
- completed-bar filtering;
- feature contract;
- ML inference;
- signal ensemble;
- DSS governance gate;
- risk engine.

## Required evidence

Record at minimum:
- model version;
- instrument;
- timestamp;
- input data snapshot/version;
- model probability;
- raw analytical direction;
- DSS action;
- reference entry;
- simulated fill;
- spread/slippage assumption;
- stop loss;
- take profit;
- outcome;
- reason for any human override.

Paper trading evidence is operational validation. It is not a guarantee of
future live performance.

The repository must not create a live approval record until the required
validation evidence and human approval are complete.
