"""Unit tests for cleaning helpers."""

from src.processing.cleaner import (
    clean_raw_product,
    compute_discount_percentage,
    is_valid_url,
    parse_currency,
    parse_rating,
    parse_review_count,
)
from src.processing.normalizer import (
    build_group_key,
    drop_duplicate_products,
    normalize_platform,
    normalize_product_name,
)


def test_parse_currency_inr_examples() -> None:
    assert parse_currency("₹7,499") == 7499.0
    assert parse_currency("₹ 12,999") == 12999.0
    assert parse_currency("Rs. 899") == 899.0
    assert parse_currency("INR 1,299.50") == 1299.50
    assert parse_currency(None) is None
    assert parse_currency("0") is None
    assert parse_currency(-10) is None


def test_parse_rating() -> None:
    assert parse_rating("4.3 out of 5") == 4.3
    assert parse_rating("4.0/5") == 4.0
    assert parse_rating(4.8) == 4.8
    assert parse_rating("9.1") is None
    assert parse_rating("") is None


def test_parse_review_count() -> None:
    assert parse_review_count("2.4K") == 2400
    assert parse_review_count("1.2M") == 1_200_000
    assert parse_review_count("1,234") == 1234
    assert parse_review_count(10) == 10
    assert parse_review_count(None) is None


def test_url_and_name_normalization() -> None:
    assert is_valid_url("https://www.amazon.in/dp/ABC")
    assert not is_valid_url("not-a-url")
    assert normalize_product_name("  Sony   WH-1000XM5  ") == "Sony WH-1000XM5"
    assert normalize_platform("amazon.in") == "Amazon"
    assert normalize_platform("flipkart") == "Flipkart"


def test_discount_and_group_key() -> None:
    assert compute_discount_percentage(7499, 9999) == 25.0
    assert compute_discount_percentage(12000, 10000) == 0.0
    assert build_group_key("Sony WH-1000XM5 Wireless Headphones") == "sony-wh-1000xm5-headphones"


def test_clean_raw_product_drops_invalid_price() -> None:
    raw = {
        "product_name": "Demo",
        "platform": "Amazon",
        "product_url": "https://www.amazon.in/dp/DEMO",
        "current_price": "not-a-price",
    }
    assert clean_raw_product(raw) is None


def test_clean_raw_product_success() -> None:
    raw = {
        "product_name": "  Demo Headphones ",
        "platform": "Amazon",
        "product_url": "https://www.amazon.in/dp/DEMO",
        "current_price": "₹7,499",
        "original_price": "₹9,999",
        "rating": "4.3 out of 5",
        "review_count": "2.4K",
        "data_origin": "synthetic",
    }
    cleaned = clean_raw_product(raw)
    assert cleaned is not None
    assert cleaned["current_price"] == 7499.0
    assert cleaned["review_count"] == 2400
    assert cleaned["discount_percentage"] == 25.0


def test_drop_duplicate_products() -> None:
    rows = [
        {"platform": "Amazon", "product_url": "https://example.com/a", "product_name": "A"},
        {"platform": "Amazon", "product_url": "https://example.com/a", "product_name": "A2"},
    ]
    unique = drop_duplicate_products(rows)
    assert len(unique) == 1
    assert unique[0]["product_name"] == "A2"
