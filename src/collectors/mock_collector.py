"""Synthetic marketplace collector for demos and tests.

All records are labeled data_origin='synthetic'. Never treat this as live
marketplace data.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pandas as pd

from src.collectors.base_collector import BaseCollector
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MockCollector(BaseCollector):
    platform_name = "Mock"
    homepage = "https://example.invalid"

    def __init__(self, catalog_path: Path | None = None) -> None:
        super().__init__()
        self.catalog_path = catalog_path or settings.sample_products_path
        self.catalog = self._load_catalog()

    def search_product(self, query: str) -> list[dict[str, Any]]:
        tokens = [token for token in query.lower().split() if token]
        if not tokens:
            return []
        ranked: list[tuple[int, dict[str, Any]]] = []
        for row in self.catalog:
            name = str(row["product_name"]).lower()
            hits = sum(1 for token in tokens if token in name)
            if hits == len(tokens) or (len(tokens) == 1 and hits == 1) or hits >= max(2, len(tokens) - 1):
                ranked.append((hits, self._to_raw(row)))
        ranked.sort(key=lambda item: item[0], reverse=True)
        matches = [row for _, row in ranked]
        if not matches:
            logger.info("No synthetic catalog match for %r; returning empty set.", query)
        return matches

    def get_product_details(self, url: str) -> dict[str, Any] | None:
        for row in self.catalog:
            if str(row["product_url"]).rstrip("/") == url.rstrip("/"):
                return self._to_raw(row)
        path = urlparse(url).path.lower()
        for row in self.catalog:
            if path and path in str(row["product_url"]).lower():
                return self._to_raw(row)
        return None

    def historical_observations(
        self,
        product_name: str,
        platform: str,
        current_price: float,
        original_price: float | None,
        days: int = 12,
    ) -> list[dict[str, Any]]:
        """Deterministic synthetic history so charts work without live feeds."""
        seed = int(hashlib.sha256(f"{product_name}|{platform}".encode()).hexdigest()[:8], 16)
        points: list[dict[str, Any]] = []
        for offset in range(days, 0, -1):
            wave = ((seed + offset * 17) % 9) - 4
            price = round(max(current_price * (1 + wave / 80), 1.0), 2)
            recorded_at = datetime.now(timezone.utc) - timedelta(days=offset)
            mrp = original_price
            discount = None
            if mrp and mrp > 0:
                discount = round((mrp - price) / mrp * 100, 2)
            points.append(
                {
                    "price": price,
                    "mrp": mrp,
                    "discount_percentage": discount,
                    "recorded_at": recorded_at,
                }
            )
        return points

    def _load_catalog(self) -> list[dict[str, Any]]:
        if self.catalog_path.exists():
            frame = pd.read_csv(self.catalog_path)
            records = frame.to_dict(orient="records")
            logger.info("Loaded %s synthetic catalog rows from %s", len(records), self.catalog_path)
            return records
        logger.warning("Sample catalog missing at %s; using built-in fallback.", self.catalog_path)
        return [
            {
                "product_name": "Demo Wireless Headphones",
                "platform": "Amazon",
                "product_url": "https://www.amazon.in/dp/DEMOHEADPHONES",
                "current_price": 4999,
                "original_price": 7999,
                "rating": 4.2,
                "review_count": 1200,
                "seller": "Demo Seller",
                "availability": "In Stock",
                "image_url": "https://placehold.co/400x400?text=Demo",
                "currency": "INR",
            }
        ]

    def _to_raw(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "product_name": row.get("product_name"),
            "platform": row.get("platform"),
            "product_url": row.get("product_url"),
            "current_price": row.get("current_price"),
            "original_price": row.get("original_price"),
            "rating": row.get("rating"),
            "review_count": row.get("review_count"),
            "seller": row.get("seller"),
            "availability": row.get("availability"),
            "image_url": row.get("image_url"),
            "currency": row.get("currency") or "INR",
            "data_origin": "synthetic",
        }
