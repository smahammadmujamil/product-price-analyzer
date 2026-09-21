"""Transparent buying recommendations derived from comparable prices."""

from __future__ import annotations

from typing import Any, Optional


def recommend_action(
    *,
    cheapest_platform: Optional[str],
    cheapest_price: Optional[float],
    amazon_minus_flipkart: Optional[float],
    historical_stats_by_platform: dict[str, dict[str, Any]],
    availability_by_platform: dict[str, Optional[str]],
) -> dict[str, Any]:
    """Return a recommendation with the rules that produced it.

    Rules (evaluated in order):
    1. If no comparable prices exist -> no recommendation.
    2. If the cheapest listing is out of stock -> prefer the next in-stock platform.
    3. If current cheapest price is within 2% of that platform's historical minimum
       AND discount is not required -> Buy now on cheapest platform.
    4. If current price is more than 5% above the historical average on the cheapest
       platform -> Wait; price is elevated versus recent history.
    5. Otherwise -> Buy on the cheapest in-stock platform.
    """
    if not cheapest_platform or cheapest_price is None:
        return {
            "action": "No recommendation",
            "headline": "Not enough comparable prices yet.",
            "reasons": ["Need at least one valid positive price observation."],
            "suggested_platform": None,
        }

    in_stock_platforms = [
        platform
        for platform, status in availability_by_platform.items()
        if status and "out of stock" not in status.lower()
    ]
    suggested = cheapest_platform
    if cheapest_platform not in in_stock_platforms and in_stock_platforms:
        suggested = in_stock_platforms[0]

    stats = historical_stats_by_platform.get(suggested) or historical_stats_by_platform.get(
        cheapest_platform, {}
    )
    current = stats.get("current_price") or cheapest_price
    hist_min = stats.get("min_historical_price")
    hist_avg = stats.get("average_historical_price")
    reasons: list[str] = []

    if amazon_minus_flipkart is not None:
        if amazon_minus_flipkart > 0:
            reasons.append(
                f"Amazon is ₹{amazon_minus_flipkart:,.2f} more expensive than Flipkart "
                "(Amazon price − Flipkart price)."
            )
        elif amazon_minus_flipkart < 0:
            reasons.append(
                f"Amazon is ₹{abs(amazon_minus_flipkart):,.2f} cheaper than Flipkart "
                "(Amazon price − Flipkart price)."
            )
        else:
            reasons.append("Amazon and Flipkart currently list the same comparable price.")

    reasons.append(f"Lowest comparable price is ₹{cheapest_price:,.2f} on {cheapest_platform}.")
    if suggested != cheapest_platform:
        reasons.append(
            f"{cheapest_platform} has the lowest nominal price (₹{cheapest_price:,.2f}) "
            f"but is currently marked as out of stock. Suggesting in-stock {suggested} instead."
        )

    if hist_min and current <= hist_min * 1.02:
        return {
            "action": "Buy now",
            "headline": f"Buy now on {suggested} — price is near the tracked low.",
            "reasons": reasons
            + [
                f"Current ₹{current:,.2f} is within 2% of the historical minimum ₹{hist_min:,.2f}.",
            ],
            "suggested_platform": suggested,
        }

    if hist_avg and current > hist_avg * 1.05:
        return {
            "action": "Wait",
            "headline": f"Consider waiting — {suggested} is above the recent average.",
            "reasons": reasons
            + [
                f"Current ₹{current:,.2f} is more than 5% above the average ₹{hist_avg:,.2f}.",
            ],
            "suggested_platform": suggested,
        }

    return {
        "action": "Buy on cheapest platform",
        "headline": f"{suggested} currently offers the better comparable price.",
        "reasons": reasons,
        "suggested_platform": suggested,
    }
