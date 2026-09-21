"""Reusable cleaning functions for marketplace fields."""

from __future__ import annotations

import math
import re
from typing import Any, Optional
from urllib.parse import urlparse

_CURRENCY_RE = re.compile(
    r"(?:₹|rs\.?|inr|usd|\$|€|£)\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"([0-9][0-9,]*(?:\.[0-9]+)?)")
_RATING_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*(?:out of\s*5|/5|stars?)?", re.IGNORECASE)
_REVIEW_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*([kmb])?", re.IGNORECASE)


def normalize_whitespace(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def parse_currency(value: Any) -> Optional[float]:
    """Convert marketplace price strings to a float.

    Examples:
        ₹7,499 -> 7499.0
        ₹ 12,999 -> 12999.0
        Rs. 899 -> 899.0
    """
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isnan(float(value)):
            return None
        amount = float(value)
        return amount if amount > 0 else None

    text = normalize_whitespace(value).replace("\u20b9", "₹")
    if not text:
        return None
    match = _CURRENCY_RE.search(text)
    raw = match.group(1) if match else None
    if raw is None:
        number = _NUMBER_RE.search(text)
        raw = number.group(1) if number else None
    if raw is None:
        return None
    try:
        amount = float(raw.replace(",", ""))
    except ValueError:
        return None
    return amount if amount > 0 else None


def parse_rating(value: Any) -> Optional[float]:
    """Convert rating strings such as '4.3 out of 5' to 4.3."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        rating = float(value)
        return rating if 0 <= rating <= 5 else None
    text = normalize_whitespace(value)
    match = _RATING_RE.search(text)
    if not match:
        return None
    rating = float(match.group(1))
    return rating if 0 <= rating <= 5 else None


def parse_review_count(value: Any) -> Optional[int]:
    """Convert compact counts such as 2.4K and 1.2M to integers."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        if math.isnan(value) or value < 0:
            return None
        return int(value)
    text = normalize_whitespace(value).replace(",", "")
    match = _REVIEW_RE.search(text)
    if not match:
        return None
    number = float(match.group(1))
    suffix = (match.group(2) or "").lower()
    multipliers = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
    count = int(number * multipliers.get(suffix, 1))
    return count if count >= 0 else None


def is_valid_url(value: Any) -> bool:
    text = normalize_whitespace(value)
    parsed = urlparse(text)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def compute_discount_percentage(price: Optional[float], mrp: Optional[float]) -> Optional[float]:
    """discount_percentage = (mrp - price) / mrp * 100, when mrp > 0 and price <= mrp."""
    if price is None or mrp is None or mrp <= 0:
        return None
    if price > mrp:
        return 0.0
    return round((mrp - price) / mrp * 100.0, 2)


def clean_raw_product(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Validate and type-coerce a collector payload. Invalid prices are dropped."""
    name = normalize_whitespace(raw.get("product_name"))
    platform = normalize_whitespace(raw.get("platform"))
    url = normalize_whitespace(raw.get("product_url"))
    price = parse_currency(raw.get("current_price"))
    if not name or not platform or not is_valid_url(url) or price is None:
        return None

    mrp = parse_currency(raw.get("original_price") or raw.get("mrp"))
    rating = parse_rating(raw.get("rating"))
    reviews = parse_review_count(raw.get("review_count"))
    origin = normalize_whitespace(raw.get("data_origin")) or "synthetic"
    availability = normalize_whitespace(raw.get("availability")) or None
    seller = normalize_whitespace(raw.get("seller")) or None
    image_url = normalize_whitespace(raw.get("image_url")) or None
    if image_url and not is_valid_url(image_url):
        image_url = None
    currency = normalize_whitespace(raw.get("currency")) or "INR"

    discount = raw.get("discount_percentage")
    if discount is not None:
        try:
            discount = float(discount)
        except (TypeError, ValueError):
            discount = None
    if discount is None:
        discount = compute_discount_percentage(price, mrp)

    return {
        "product_name": name,
        "platform": platform,
        "product_url": url,
        "current_price": price,
        "original_price": mrp,
        "discount_percentage": discount,
        "rating": rating,
        "review_count": reviews,
        "seller": seller,
        "availability": availability,
        "image_url": image_url,
        "currency": currency.upper(),
        "data_origin": origin.lower(),
    }
