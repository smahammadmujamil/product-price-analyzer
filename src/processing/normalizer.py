"""Normalization so the same product can be compared across platforms."""

from __future__ import annotations

import re
from typing import Any

from src.processing.cleaner import normalize_whitespace

STOPWORDS = {
    "with",
    "and",
    "for",
    "the",
    "a",
    "an",
    "new",
    "gen",
    "generation",
    "wireless",
    "bluetooth",
}

PLATFORM_ALIASES = {
    "amazon": "Amazon",
    "amazon.in": "Amazon",
    "amazon.com": "Amazon",
    "flipkart": "Flipkart",
    "fk": "Flipkart",
    "myntra": "Myntra",
    "croma": "Croma",
    "reliance digital": "Reliance Digital",
    "reliancedigital": "Reliance Digital",
    "mock": "Mock",
}


def normalize_platform(value: Any) -> str:
    text = normalize_whitespace(value).lower()
    return PLATFORM_ALIASES.get(text, normalize_whitespace(value).title() or "Unknown")


def normalize_product_name(value: Any) -> str:
    text = normalize_whitespace(value)
    text = re.sub(r"[\(\)\[\]\{\}|,]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_group_key(product_name: str) -> str:
    """Stable comparison key from significant name tokens."""
    tokens = re.findall(r"[a-z0-9]+", product_name.lower())
    kept = [token for token in tokens if token not in STOPWORDS and len(token) > 1]
    if not kept:
        kept = tokens
    return "-".join(kept[:8])


def drop_duplicate_products(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep one record per platform + URL, last write wins."""
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        key = (record["platform"], record["product_url"])
        unique[key] = record
    return list(unique.values())


def normalize_record(cleaned: dict[str, Any]) -> dict[str, Any]:
    name = normalize_product_name(cleaned["product_name"])
    platform = normalize_platform(cleaned["platform"])
    return {
        **cleaned,
        "product_name": name,
        "platform": platform,
        "group_key": build_group_key(name),
    }
