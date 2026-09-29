"""Transaction-cost sensitivity checks for research validation."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostScenario:
    spread: float
    slippage: float
    commission: float = 0.0

    @property
    def round_trip_cost(self) -> float:
        return max(0.0, 2.0 * self.spread + 2.0 * self.slippage + self.commission)


def net_return(gross_return: float, scenario: CostScenario) -> float:
    return float(gross_return) - scenario.round_trip_cost


def sensitivity(gross_returns: list[float], scenarios: list[CostScenario]) -> dict[str, dict[str, float]]:
    if not gross_returns or not scenarios:
        raise ValueError("gross_returns and scenarios must not be empty")
    return {
        f"spread={s.spread:g};slippage={s.slippage:g};commission={s.commission:g}": {
            "mean_net_return": sum(net_return(x, s) for x in gross_returns) / len(gross_returns),
            "min_net_return": min(net_return(x, s) for x in gross_returns),
            "positive_fraction": sum(net_return(x, s) > 0 for x in gross_returns) / len(gross_returns),
        }
        for s in scenarios
    }
