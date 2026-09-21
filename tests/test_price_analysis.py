"""Unit tests for price analysis formulas."""

import math

from src.analytics.price_analysis import (
    compare_platforms,
    compute_historical_stats,
    compute_percentage_difference,
    compute_price_difference,
    identify_cheapest_platform,
)
from src.analytics.recommendations import recommend_action


def test_price_difference() -> None:
    assert compute_price_difference(7499, 7299) == 200
    assert compute_price_difference(7299, 7499) == -200


def test_percentage_difference_mean_reference() -> None:
    result = compute_percentage_difference(110, 90, reference="mean")
    # ((110-90)/100)*100 = 20
    assert math.isclose(result, 20.0)


def test_percentage_difference_vs_b() -> None:
    result = compute_percentage_difference(110, 100, reference="b")
    assert math.isclose(result, 10.0)


def test_cheapest_platform() -> None:
    platform, price = identify_cheapest_platform({"Amazon": 24990, "Flipkart": 23990})
    assert platform == "Flipkart"
    assert price == 23990
    assert identify_cheapest_platform({"Amazon": None}) == (None, None)


def test_historical_stats() -> None:
    stats = compute_historical_stats([100, 110, 90, 95])
    assert stats["current_price"] == 95
    assert stats["min_historical_price"] == 90
    assert stats["max_historical_price"] == 110
    assert stats["average_historical_price"] == 98.75
    assert stats["price_change"] == 5
    assert math.isclose(stats["price_change_percentage"] or 0, (5 / 90) * 100)
    assert stats["observation_count"] == 4
    assert stats["price_volatility"] is not None


def test_compare_platforms() -> None:
    comparison = compare_platforms(
        [
            {"platform": "Amazon", "price": 7499},
            {"platform": "Flipkart", "price": 7299},
        ]
    )
    assert comparison["amazon_minus_flipkart"] == 200
    assert comparison["cheapest_platform"] == "Flipkart"


def test_recommend_buy_near_low() -> None:
    rec = recommend_action(
        cheapest_platform="Flipkart",
        cheapest_price=7200,
        amazon_minus_flipkart=200,
        historical_stats_by_platform={
            "Flipkart": {"current_price": 7200, "min_historical_price": 7190, "average_historical_price": 7800}
        },
        availability_by_platform={"Flipkart": "In Stock", "Amazon": "In Stock"},
    )
    assert rec["action"] == "Buy now"


def test_recommend_wait_when_elevated() -> None:
    rec = recommend_action(
        cheapest_platform="Amazon",
        cheapest_price=9000,
        amazon_minus_flipkart=-100,
        historical_stats_by_platform={
            "Amazon": {"current_price": 9000, "min_historical_price": 7000, "average_historical_price": 8000}
        },
        availability_by_platform={"Amazon": "In Stock"},
    )
    assert rec["action"] == "Wait"
