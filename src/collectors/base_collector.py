"""Abstract marketplace collector and shared HTTP helpers."""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CollectorError(Exception):
    """Raised when a collector cannot return data through permitted channels."""


class CollectorBlockedError(CollectorError):
    """Raised when robots.txt, HTTP status, or access controls block collection."""


class BaseCollector(ABC):
    """Contract for marketplace collectors.

    Implementations must not bypass CAPTCHA, authentication, anti-bot systems,
    rate limits, or robots.txt. Prefer official partner APIs when credentials
    are provided. Live HTML access is best-effort and may return no results.
    """

    platform_name: str = "unknown"
    homepage: str = ""

    def __init__(self) -> None:
        self.timeout = settings.request_timeout_seconds
        self.delay_seconds = settings.request_delay_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": settings.user_agent,
                "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-IN,en;q=0.8",
            }
        )
        self._last_request_at = 0.0

    @abstractmethod
    def search_product(self, query: str) -> list[dict[str, Any]]:
        """Return raw product dictionaries for a search query."""

    @abstractmethod
    def get_product_details(self, url: str) -> dict[str, Any] | None:
        """Return a raw product dictionary for a product URL."""

    _robots_cache: dict[str, RobotFileParser] = {}

    def respects_robots(self, url: str) -> bool:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc in self._robots_cache:
            return self._robots_cache[netloc].can_fetch(settings.user_agent, url)

        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            resp = self.session.get(robots_url, timeout=self.timeout)
            parser = RobotFileParser()
            parser.set_url(robots_url)
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            elif resp.status_code in {401, 403}:
                # Access denied to robots.txt -> disallow by default
                parser.parse(["User-agent: *", "Disallow: /"])
            else:
                # 404 or missing robots.txt -> allow
                parser.parse([])
            self._robots_cache[netloc] = parser
            allowed = parser.can_fetch(settings.user_agent, url)
            if not allowed:
                logger.warning("robots.txt disallows %s for %s", url, settings.user_agent)
            return allowed
        except Exception as exc:  # noqa: BLE001
            logger.info("Could not read robots.txt at %s (%s). Skipping live fetch.", robots_url, exc)
            return False

    def polite_get(self, url: str) -> requests.Response:
        if not self.respects_robots(url):
            raise CollectorBlockedError(f"Fetch not permitted for {url}")
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)
        response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
        self._last_request_at = time.monotonic()
        if response.status_code in {401, 403, 429, 503}:
            raise CollectorBlockedError(
                f"{self.platform_name} returned HTTP {response.status_code}; access controls were respected."
            )
        if response.status_code >= 400:
            raise CollectorError(f"{self.platform_name} HTTP {response.status_code} for {url}")
        lowered = response.text.lower()
        if "captcha" in lowered and "robot" in lowered:
            raise CollectorBlockedError(
                f"{self.platform_name} presented an access challenge. No bypass was attempted."
            )
        return response

    def extract_json_ld_products(self, html: str) -> list[dict[str, Any]]:
        """Parse public schema.org Product JSON-LD only."""
        soup = BeautifulSoup(html, "lxml")
        products: list[dict[str, Any]] = []
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            text = script.string or script.get_text() or ""
            if not text.strip():
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            blocks = payload if isinstance(payload, list) else [payload]
            for block in blocks:
                products.extend(self._json_ld_to_raw(block))
        return products[:8]

    def _json_ld_to_raw(self, block: Any) -> list[dict[str, Any]]:
        if not isinstance(block, dict):
            return []
        graph = block.get("@graph")
        if isinstance(graph, list):
            found: list[dict[str, Any]] = []
            for node in graph:
                found.extend(self._json_ld_to_raw(node))
            return found
        types = block.get("@type")
        type_list = types if isinstance(types, list) else [types]
        if "ItemList" in {str(item) for item in type_list if item}:
            found = []
            for element in block.get("itemListElement") or []:
                if isinstance(element, dict):
                    found.extend(self._json_ld_to_raw(element.get("item") or element))
            return found
        if "Product" not in {str(item) for item in type_list if item}:
            return []
        offers = block.get("offers") or {}
        if isinstance(offers, list) and offers:
            offers = offers[0]
        if not isinstance(offers, dict):
            offers = {}
        rating = block.get("aggregateRating") or {}
        url = block.get("url") or offers.get("url")
        if not url:
            return []
        return [
            {
                "product_name": block.get("name"),
                "platform": self.platform_name,
                "product_url": url,
                "current_price": offers.get("price"),
                "original_price": None,
                "rating": rating.get("ratingValue") if isinstance(rating, dict) else None,
                "review_count": rating.get("reviewCount") if isinstance(rating, dict) else None,
                "seller": (offers.get("seller") or {}).get("name")
                if isinstance(offers.get("seller"), dict)
                else None,
                "availability": offers.get("availability"),
                "image_url": block.get("image") if isinstance(block.get("image"), str) else None,
                "currency": offers.get("priceCurrency") or "INR",
                "data_origin": "live",
            }
        ]
