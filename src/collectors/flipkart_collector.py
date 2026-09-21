"""Flipkart collector.

Uses the official affiliate/product API only when credentials are provided.
Does not bypass access controls. Public HTML is attempted politely and fails closed.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

from src.collectors.base_collector import (
    BaseCollector,
    CollectorBlockedError,
    CollectorError,
)
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FlipkartCollector(BaseCollector):
    platform_name = "Flipkart"
    homepage = "https://www.flipkart.com"

    def search_product(self, query: str) -> list[dict[str, Any]]:
        if settings.flipkart_official_api_configured:
            return self._search_affiliate_api(query)

        search_url = f"{self.homepage}/search?q={quote_plus(query)}"
        try:
            response = self.polite_get(search_url)
        except (CollectorBlockedError, CollectorError) as exc:
            logger.info("Flipkart search unavailable through permitted access: %s", exc)
            return []

        products = self.extract_json_ld_products(response.text)
        logger.info("Flipkart JSON-LD produced %s public product records.", len(products))
        return products

    def get_product_details(self, url: str) -> dict[str, Any] | None:
        if "flipkart." not in url.lower():
            return None
        if settings.flipkart_official_api_configured:
            logger.info("Affiliate API product-by-URL is not implemented in this portfolio build.")
            return None
        try:
            response = self.polite_get(url)
        except (CollectorBlockedError, CollectorError) as exc:
            logger.info("Flipkart product details unavailable through permitted access: %s", exc)
            return None
        products = self.extract_json_ld_products(response.text)
        return products[0] if products else None

    def _search_affiliate_api(self, query: str) -> list[dict[str, Any]]:
        """Permitted affiliate search. Returns empty if the program endpoint rejects the call."""
        endpoint = (
            "https://affiliate-api.flipkart.net/affiliate/search/json"
            f"?query={quote_plus(query)}&resultCount=5"
        )
        headers = {
            "Fk-Affiliate-Id": settings.flipkart_affiliate_id or "",
            "Fk-Affiliate-Token": settings.flipkart_affiliate_token or "",
        }
        try:
            response = self.session.get(endpoint, headers=headers, timeout=self.timeout)
        except Exception as exc:  # noqa: BLE001
            logger.info("Flipkart affiliate API request failed: %s", exc)
            return []
        if response.status_code >= 400:
            logger.info("Flipkart affiliate API HTTP %s", response.status_code)
            return []
        payload = response.json()
        products = payload.get("products") or []
        parsed: list[dict[str, Any]] = []
        for item in products:
            info = (item.get("productBaseInfoV1") or item) if isinstance(item, dict) else {}
            parsed.append(
                {
                    "product_name": info.get("title") or query,
                    "platform": "Flipkart",
                    "product_url": (info.get("productUrl") or {}).get("seeAll")
                    if isinstance(info.get("productUrl"), dict)
                    else info.get("productUrl") or self.homepage,
                    "current_price": (info.get("flipkartSpecialPrice") or {}).get("amount")
                    if isinstance(info.get("flipkartSpecialPrice"), dict)
                    else info.get("sellingPrice"),
                    "original_price": (info.get("maximumRetailPrice") or {}).get("amount")
                    if isinstance(info.get("maximumRetailPrice"), dict)
                    else info.get("mrp"),
                    "rating": info.get("averageRating"),
                    "review_count": info.get("totalRatings"),
                    "seller": None,
                    "availability": info.get("inStock"),
                    "image_url": None,
                    "currency": "INR",
                    "data_origin": "live",
                }
            )
        return parsed
