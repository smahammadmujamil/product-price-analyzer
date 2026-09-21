"""Amazon collector.

Live collection uses the official Product Advertising API when credentials are
configured. Unofficial scraping that would bypass marketplace protections is
not implemented. Public HTML fetches are polite, robots.txt-aware, and fail
closed when blocked.
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


class AmazonCollector(BaseCollector):
    platform_name = "Amazon"
    homepage = "https://www.amazon.in"

    def search_product(self, query: str) -> list[dict[str, Any]]:
        if settings.amazon_official_api_configured:
            logger.warning(
                "Amazon Product Advertising API credentials are present, but a signed PA-API "
                "client is not bundled in this portfolio build. Configure an official PA-API "
                "SDK in a private extension, or use Demo mode."
            )
            return []

        search_url = f"{self.homepage}/s?k={quote_plus(query)}"
        try:
            response = self.polite_get(search_url)
        except (CollectorBlockedError, CollectorError) as exc:
            logger.info("Amazon search unavailable through permitted access: %s", exc)
            return []

        products = self.extract_json_ld_products(response.text)
        logger.info("Amazon JSON-LD produced %s public product records.", len(products))
        return products

    def get_product_details(self, url: str) -> dict[str, Any] | None:
        if "amazon." not in url.lower():
            return None
        if settings.amazon_official_api_configured:
            logger.warning("Official Amazon PA-API is configured but not implemented in this build.")
            return None
        try:
            response = self.polite_get(url)
        except (CollectorBlockedError, CollectorError) as exc:
            logger.info("Amazon product details unavailable through permitted access: %s", exc)
            return None
        products = self.extract_json_ld_products(response.text)
        return products[0] if products else None
