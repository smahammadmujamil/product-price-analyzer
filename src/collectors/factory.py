"""Collector factory so new marketplaces can be registered without changing callers."""

from __future__ import annotations

from src.collectors.amazon_collector import AmazonCollector
from src.collectors.base_collector import BaseCollector
from src.collectors.flipkart_collector import FlipkartCollector
from src.collectors.mock_collector import MockCollector
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

COLLECTOR_REGISTRY: dict[str, type[BaseCollector]] = {
    "amazon": AmazonCollector,
    "flipkart": FlipkartCollector,
    "mock": MockCollector,
    # Future: "myntra": MyntraCollector,
    # Future: "croma": CromaCollector,
    # Future: "reliance_digital": RelianceDigitalCollector,
}


class CollectorFactory:
    @staticmethod
    def create(name: str) -> BaseCollector:
        key = name.strip().lower()
        if key not in COLLECTOR_REGISTRY:
            raise KeyError(
                f"Unknown collector '{name}'. Registered: {sorted(COLLECTOR_REGISTRY)}"
            )
        return COLLECTOR_REGISTRY[key]()

    @staticmethod
    def register(name: str, collector_cls: type[BaseCollector]) -> None:
        COLLECTOR_REGISTRY[name.strip().lower()] = collector_cls

    @staticmethod
    def default_collectors(data_source: str | None = None) -> list[BaseCollector]:
        source = (data_source or settings.data_source).lower()
        if source == "mock":
            logger.info("Using MockCollector. Results are synthetic demonstration data.")
            return [MockCollector()]
        logger.info("Live mode: attempting permitted Amazon and Flipkart collectors.")
        return [AmazonCollector(), FlipkartCollector()]
