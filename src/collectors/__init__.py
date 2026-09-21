"""Collectors package. Register new marketplaces in the factory."""

from src.collectors.amazon_collector import AmazonCollector
from src.collectors.base_collector import BaseCollector
from src.collectors.factory import CollectorFactory
from src.collectors.flipkart_collector import FlipkartCollector
from src.collectors.mock_collector import MockCollector

__all__ = [
    "AmazonCollector",
    "BaseCollector",
    "CollectorFactory",
    "FlipkartCollector",
    "MockCollector",
]
