"""Analytics package."""

from src.analytics.price_analysis import (
    compare_platforms,
    compute_historical_stats,
    compute_percentage_difference,
    compute_price_difference,
    identify_cheapest_platform,
)
from src.analytics.recommendations import recommend_action

__all__ = [
    "compare_platforms",
    "compute_historical_stats",
    "compute_percentage_difference",
    "compute_price_difference",
    "identify_cheapest_platform",
    "recommend_action",
]
