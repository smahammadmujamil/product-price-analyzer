"""Unit and integration tests for the pipeline, collectors, and end-to-end execution."""

from unittest.mock import MagicMock

from src.collectors.base_collector import BaseCollector
from src.collectors.factory import CollectorFactory
from src.collectors.mock_collector import MockCollector
from src.models import ProductObservation
from src.pipeline import collect_raw, run_search, select_primary_group


def test_select_primary_group_empty() -> None:
    assert select_primary_group([], "Sony") is None


def test_select_primary_group_no_group_key() -> None:
    obs = [
        ProductObservation(
            product_name="Product Without Key",
            platform="Amazon",
            product_url="https://www.amazon.in/dp/DEMO",
            current_price=100.0,
            group_key=None,
        )
    ]
    assert select_primary_group(obs, "query") is None


def test_select_primary_group_scoring() -> None:
    obs1 = ProductObservation(
        product_name="Sony WH-1000XM5 Wireless Headphones",
        platform="Amazon",
        product_url="https://www.amazon.in/dp/SONY1",
        current_price=24990.0,
        group_key="sony-wh-1000xm5-headphones",
    )
    obs2 = ProductObservation(
        product_name="Sony WH-1000XM5 Wireless Headphones",
        platform="Flipkart",
        product_url="https://www.flipkart.com/dp/SONY2",
        current_price=23990.0,
        group_key="sony-wh-1000xm5-headphones",
    )
    obs3 = ProductObservation(
        product_name="Apple iPhone 15",
        platform="Amazon",
        product_url="https://www.amazon.in/dp/IPHONE",
        current_price=69900.0,
        group_key="apple-iphone-15",
    )
    chosen = select_primary_group([obs1, obs2, obs3], "Sony XM5")
    assert chosen == "sony-wh-1000xm5-headphones"


def test_collector_factory() -> None:
    mock = CollectorFactory.create("mock")
    assert isinstance(mock, MockCollector)
    default_mock = CollectorFactory.default_collectors("mock")
    assert len(default_mock) == 1
    assert isinstance(default_mock[0], MockCollector)


def test_collect_raw_url_mock() -> None:
    mock = MockCollector()
    results = collect_raw("https://www.amazon.in/dp/DEMOWH1000XM5", [mock])
    platforms = {r["platform"] for r in results}
    assert "Amazon" in platforms
    assert "Flipkart" in platforms


def test_run_search_mock_catalog() -> None:
    res = run_search("iPhone 15", data_source="mock")
    assert res["message"] is None
    assert res["analysis"] is not None
    assert res["analysis"]["comparison"]["cheapest_platform"] in {"Amazon", "Flipkart"}
    assert res["analysis"]["latest"]
    assert res["analysis"]["recommendation"]["action"] in {
        "Buy now",
        "Wait",
        "Buy on cheapest platform",
    }


def test_base_collector_robots_cache() -> None:
    class DummyCollector(BaseCollector):
        platform_name = "Dummy"
        def search_product(self, query): return []
        def get_product_details(self, url): return None

    dummy = DummyCollector()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "User-agent: *\nDisallow: /private/\nAllow: /public/"
    dummy.session.get = MagicMock(return_value=mock_resp)

    # First call fills cache
    allowed_pub = dummy.respects_robots("https://dummy.example.com/public/item")
    assert allowed_pub is True
    assert "dummy.example.com" in dummy._robots_cache

    # Second call uses cache (session.get should not be called again)
    call_count = dummy.session.get.call_count
    allowed_priv = dummy.respects_robots("https://dummy.example.com/private/secret")
    assert allowed_priv is False
    assert dummy.session.get.call_count == call_count
