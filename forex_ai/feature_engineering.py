"""Feature engineering shared by training and inference."""
from __future__ import annotations

import pandas as pd

# Price/OHLC features are used so the live Forex provider does not depend on a
# volume field whose availability/definition can differ by provider.
FEATURES = [
    "ret_1", "ret_5", "ret_10", "ret_20",
    "vol_10", "vol_20", "range_pct",
]


def build_features(df: pd.DataFrame, horizon: int | None = None) -> pd.DataFrame:
    required = {"date", "open", "high", "low", "close"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    out = df.copy().sort_values("date").drop_duplicates("date").reset_index(drop=True)
    ret = out["close"].pct_change()
    out["ret_1"] = ret
    out["ret_5"] = out["close"].pct_change(5)
    out["ret_10"] = out["close"].pct_change(10)
    out["ret_20"] = out["close"].pct_change(20)
    out["vol_10"] = ret.rolling(10).std()
    out["vol_20"] = ret.rolling(20).std()
    out["range_pct"] = (out["high"] - out["low"]) / out["close"]
    # Kept as an optional diagnostic column for backward compatibility. It is
    # deliberately not part of FEATURES because provider volume semantics vary.
    volume = out.get("tick_volume", pd.Series(index=out.index, dtype=float))
    out["volume_change"] = pd.to_numeric(volume, errors="coerce").pct_change()
    if horizon is not None:
        forward_return = out["close"].shift(-horizon) / out["close"] - 1.0
        out["label"] = (forward_return >= 0.005).astype(int)
    return out.dropna(subset=FEATURES).copy()
