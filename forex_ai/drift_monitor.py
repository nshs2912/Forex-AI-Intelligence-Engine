"""Lightweight feature-distribution drift monitoring."""
from __future__ import annotations

import math
from typing import Iterable


def population_stability_index(expected: Iterable[float], actual: Iterable[float], bins: int = 10) -> float:
    e = list(expected)
    a = list(actual)
    if len(e) < 20 or len(a) < 20 or bins < 2:
        raise ValueError("expected and actual need >=20 observations and bins >=2")
    values = sorted(e)
    edges = [values[min(len(values) - 1, int(i * len(values) / bins))] for i in range(1, bins)]
    def counts(values):
        out = [0] * bins
        for value in values:
            idx = sum(value > edge for edge in edges)
            out[min(idx, bins - 1)] += 1
        return [max(x / len(values), 1e-6) for x in out]
    pe, pa = counts(e), counts(a)
    return float(sum((a_i - e_i) * math.log(a_i / e_i) for e_i, a_i in zip(pe, pa)))


def drift_status(psi: float) -> str:
    if psi < 0.1:
        return "stable"
    if psi < 0.25:
        return "watch"
    return "drift"
