"""Price analysis formulas.

All comparisons use comparable INR (or shared currency) prices after cleaning.
Missing values are excluded rather than imputed.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

import numpy as np
import pandas as pd


def compute_price_difference(price_a: float, price_b: float) -> float:
    """Absolute signed gap.

    price_difference = price_a - price_b

    Example: Amazon 7499 - Flipkart 7299 = 200
    A positive result means A is more expensive than B.
    """
    return float(price_a) - float(price_b)


def compute_percentage_difference(
    price_a: float,
    price_b: float,
    reference: str = "mean",
) -> float:
    """Percentage difference relative to a documented reference price.

    If reference == 'mean' (default):
        reference_price = (price_a + price_b) / 2
        percentage_difference = (price_a - price_b) / reference_price * 100

    If reference == 'b':
        percentage_difference = (price_a - price_b) / price_b * 100

    If reference == 'a':
        percentage_difference = (price_a - price_b) / price_a * 100
    """
    a = float(price_a)
    b = float(price_b)
    if reference == "b":
        if b == 0:
            raise ValueError("Reference price B is zero.")
        return (a - b) / b * 100.0
    if reference == "a":
        if a == 0:
            raise ValueError("Reference price A is zero.")
        return (a - b) / a * 100.0
    mean = (a + b) / 2.0
    if mean == 0:
        raise ValueError("Mean reference price is zero.")
    return (a - b) / mean * 100.0


def identify_cheapest_platform(
    platform_prices: dict[str, Optional[float]],
) -> tuple[str | None, float | None]:
    """Return the platform with the lowest positive price."""
    valid = {
        platform: float(price)
        for platform, price in platform_prices.items()
        if price is not None and price > 0
    }
    if not valid:
        return None, None
    platform = min(valid, key=valid.get)
    return platform, valid[platform]


def compute_historical_stats(prices: Iterable[float]) -> dict[str, Optional[float]]:
    """Statistics for a single platform's ordered price series (oldest -> newest).

    current_price          = last observation
    min_historical_price   = min(prices)
    max_historical_price   = max(prices)
    average_historical_price = mean(prices)
    price_change           = current - previous
    price_change_percentage = (current - previous) / previous * 100
    price_volatility       = sample_std(prices) / mean(prices)  (coefficient of variation)
    """
    series = [float(p) for p in prices if p is not None]
    if not series:
        return {
            "current_price": None,
            "min_historical_price": None,
            "max_historical_price": None,
            "average_historical_price": None,
            "price_change": None,
            "price_change_percentage": None,
            "price_volatility": None,
            "observation_count": 0,
        }

    current = series[-1]
    previous = series[-2] if len(series) > 1 else None
    mean = float(np.mean(series))
    change = current - previous if previous is not None else None
    change_pct = (change / previous * 100.0) if previous not in (None, 0) and change is not None else None
    volatility = None
    if len(series) >= 2 and mean != 0:
        volatility = float(np.std(series, ddof=1) / mean)

    return {
        "current_price": current,
        "min_historical_price": float(np.min(series)),
        "max_historical_price": float(np.max(series)),
        "average_historical_price": mean,
        "price_change": change,
        "price_change_percentage": change_pct,
        "price_volatility": volatility,
        "observation_count": len(series),
    }


def compare_platforms(latest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a cross-platform comparison from latest price rows."""
    by_platform = {row["platform"]: row for row in latest_rows}
    amazon = by_platform.get("Amazon")
    flipkart = by_platform.get("Flipkart")
    prices = {row["platform"]: row.get("price") for row in latest_rows}
    cheapest_platform, cheapest_price = identify_cheapest_platform(prices)

    difference = None
    pct = None
    if amazon and flipkart and amazon.get("price") and flipkart.get("price"):
        difference = compute_price_difference(amazon["price"], flipkart["price"])
        pct = compute_percentage_difference(amazon["price"], flipkart["price"], reference="mean")

    return {
        "by_platform": by_platform,
        "amazon_minus_flipkart": difference,
        "percentage_difference_vs_mean": pct,
        "cheapest_platform": cheapest_platform,
        "cheapest_price": cheapest_price,
        "platform_count": len(by_platform),
    }


def history_frame(history_rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not history_rows:
        return pd.DataFrame(columns=["recorded_at", "platform", "price", "mrp", "discount_percentage"])
    frame = pd.DataFrame(history_rows)
    frame["recorded_at"] = pd.to_datetime(frame["recorded_at"], utc=True)
    return frame.sort_values(["recorded_at", "platform"])
