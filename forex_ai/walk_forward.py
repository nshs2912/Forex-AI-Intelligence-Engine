"""Leakage-safe walk-forward validation utilities."""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

from forex_ai.feature_engineering import FEATURES, build_features


@dataclass(frozen=True)
class FoldResult:
    fold: int
    train_end: str
    test_start: str
    test_end: str
    train_rows: int
    test_rows: int
    roc_auc: float
    pr_auc: float
    brier_score: float


def make_labeled_dataset(df: pd.DataFrame, horizon: int = 5, threshold: float = 0.005) -> pd.DataFrame:
    if horizon < 1 or threshold <= 0:
        raise ValueError("horizon must be >= 1 and threshold must be > 0")
    out = build_features(df)
    future = out["close"].shift(-horizon) / out["close"] - 1.0
    out["label"] = np.where(future >= threshold, 1, np.where(future <= -threshold, 0, np.nan))
    return out.dropna(subset=FEATURES + ["label"]).assign(label=lambda x: x["label"].astype(int))


def walk_forward_validate(
    df: pd.DataFrame,
    *,
    min_train_rows: int = 500,
    test_rows: int = 100,
    step_rows: int = 100,
) -> list[FoldResult]:
    data = make_labeled_dataset(df).sort_values("date").reset_index(drop=True)
    if min_train_rows < 100 or test_rows < 20 or step_rows < 1:
        raise ValueError("invalid walk-forward parameters")
    results: list[FoldResult] = []
    fold = 0
    train_end = min_train_rows
    while train_end + test_rows <= len(data):
        train = data.iloc[:train_end]
        test = data.iloc[train_end : train_end + test_rows]
        if train["label"].nunique() < 2 or test["label"].nunique() < 2:
            train_end += step_rows
            continue
        scaler = StandardScaler().fit(train[FEATURES])
        model = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)
        model.fit(scaler.transform(train[FEATURES]), train["label"])
        score = model.predict_proba(scaler.transform(test[FEATURES]))[:, 1]
        results.append(FoldResult(
            fold=fold,
            train_end=str(train["date"].iloc[-1].date()),
            test_start=str(test["date"].iloc[0].date()),
            test_end=str(test["date"].iloc[-1].date()),
            train_rows=len(train),
            test_rows=len(test),
            roc_auc=float(roc_auc_score(test["label"], score)),
            pr_auc=float(average_precision_score(test["label"], score)),
            brier_score=float(brier_score_loss(test["label"], score)),
        ))
        fold += 1
        train_end += step_rows
    return results
