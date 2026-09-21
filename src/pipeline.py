"""End-to-end pipeline: collect → clean → normalize → store → analyze."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from src.analytics.price_analysis import (
    compare_platforms,
    compute_historical_stats,
    history_frame,
)
from src.analytics.recommendations import recommend_action
from src.collectors.base_collector import BaseCollector
from src.collectors.factory import CollectorFactory
from src.collectors.mock_collector import MockCollector
from src.database import (
    create_database,
    get_latest_prices,
    get_price_history,
    get_price_history_for_group,
    get_session,
    insert_price_history,
    insert_product,
)
from src.models import ProductObservation
from src.processing.cleaner import clean_raw_product
from src.processing.normalizer import drop_duplicate_products, normalize_record
from src.utils.logger import get_logger

logger = get_logger(__name__)


def collect_raw(query: str, collectors: list[BaseCollector] | None = None) -> list[dict[str, Any]]:
    collectors = collectors or CollectorFactory.default_collectors()
    collected: list[dict[str, Any]] = []
    looks_like_url = query.lower().startswith("http://") or query.lower().startswith("https://")
    for collector in collectors:
        try:
            if looks_like_url:
                details = collector.get_product_details(query)
                if details:
                    rows = [details]
                    if isinstance(collector, MockCollector) and details.get("product_name"):
                        more_rows = collector.search_product(details["product_name"])
                        rows.extend(more_rows)
                elif isinstance(collector, MockCollector):
                    rows = collector.search_product(query)
                else:
                    rows = []
            else:
                rows = collector.search_product(query)
            collected.extend(rows)
        except Exception as exc:  # noqa: BLE001
            logger.info("%s collector failed safely: %s", collector.platform_name, exc)
    return collected


def process_records(raw_rows: list[dict[str, Any]]) -> list[ProductObservation]:
    cleaned: list[dict[str, Any]] = []
    for raw in raw_rows:
        item = clean_raw_product(raw)
        if item:
            cleaned.append(normalize_record(item))
    cleaned = drop_duplicate_products(cleaned)
    observations: list[ProductObservation] = []
    for item in cleaned:
        try:
            observations.append(ProductObservation.model_validate(item))
        except ValidationError as exc:
            logger.info("Dropped invalid observation: %s", exc)
    return observations


def persist_observations(
    observations: list[ProductObservation],
    seed_history: bool = False,
    collectors: list[BaseCollector] | None = None,
) -> str | None:
    if not observations:
        return None
    mock = next((c for c in (collectors or []) if isinstance(c, MockCollector)), None)
    with get_session() as session:
        for obs in observations:
            product = insert_product(
                session,
                {
                    "product_name": obs.product_name,
                    "platform": obs.platform,
                    "product_url": str(obs.product_url),
                    "seller": obs.seller,
                    "rating": obs.rating,
                    "review_count": obs.review_count,
                    "availability": obs.availability,
                    "image_url": obs.image_url,
                    "group_key": obs.group_key,
                    "currency": obs.currency,
                    "data_origin": obs.data_origin,
                },
            )
            existing_history = get_price_history(session, product.id)
            if seed_history and mock and not existing_history:
                for point in mock.historical_observations(
                    obs.product_name,
                    obs.platform,
                    obs.current_price,
                    obs.original_price,
                ):
                    insert_price_history(
                        session,
                        product.id,
                        price=point["price"],
                        mrp=point["mrp"],
                        discount_percentage=point["discount_percentage"],
                        recorded_at=point["recorded_at"],
                    )
            # Avoid inserting duplicate observations within 1 hour if price and MRP are identical
            now = obs.observed_at or datetime.now(timezone.utc)
            should_record = True
            if existing_history:
                latest_point = existing_history[-1]
                same_price = (
                    latest_point.price == obs.current_price
                    and latest_point.mrp == obs.original_price
                )
                prev_time = latest_point.recorded_at
                if prev_time.tzinfo is None:
                    prev_time = prev_time.replace(tzinfo=timezone.utc)
                curr_time = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
                if same_price and abs((curr_time - prev_time).total_seconds()) < 3600:
                    should_record = False

            if should_record:
                insert_price_history(
                    session,
                    product.id,
                    price=obs.current_price,
                    mrp=obs.original_price,
                    discount_percentage=obs.discount_percentage,
                    recorded_at=obs.observed_at,
                )
    return observations[0].group_key


def select_primary_group(observations: list[ProductObservation], query: str) -> str | None:
    """Prefer a product family that appears on multiple platforms and matches the query."""
    if not observations:
        return None
    by_key: dict[str, list[ProductObservation]] = defaultdict(list)
    for obs in observations:
        if obs.group_key:
            by_key[obs.group_key].append(obs)
    if not by_key:
        return None
    tokens = {token for token in query.lower().split() if len(token) > 1}

    def score(key: str) -> tuple[int, int]:
        items = by_key[key]
        platforms = {item.platform for item in items}
        name = items[0].product_name.lower()
        overlap = sum(1 for token in tokens if token in name)
        return (len(platforms), overlap)

    return max(by_key, key=score)


def analyze_group(group_key: str) -> dict[str, Any]:
    with get_session() as session:
        latest = get_latest_prices(session, group_key=group_key)
        history = get_price_history_for_group(session, group_key)
    comparison = compare_platforms(latest)
    stats_by_platform: dict[str, dict[str, Any]] = {}
    availability = {}
    frame = history_frame(history)
    for row in latest:
        platform = row["platform"]
        series = frame.loc[frame["platform"] == platform, "price"].tolist() if not frame.empty else [row["price"]]
        stats_by_platform[platform] = compute_historical_stats(series)
        availability[platform] = row.get("availability")
    recommendation = recommend_action(
        cheapest_platform=comparison["cheapest_platform"],
        cheapest_price=comparison["cheapest_price"],
        amazon_minus_flipkart=comparison["amazon_minus_flipkart"],
        historical_stats_by_platform=stats_by_platform,
        availability_by_platform=availability,
    )
    origins = {row.get("data_origin") for row in latest}
    return {
        "group_key": group_key,
        "latest": latest,
        "history": history,
        "history_frame": frame,
        "comparison": comparison,
        "stats_by_platform": stats_by_platform,
        "recommendation": recommendation,
        "data_origin": "synthetic" if origins == {"synthetic"} else ("mixed" if len(origins) > 1 else next(iter(origins), "unknown")),
    }


def run_search(query: str, data_source: str = "mock") -> dict[str, Any]:
    create_database()
    collectors = CollectorFactory.default_collectors(data_source)
    raw = collect_raw(query, collectors)
    observations = process_records(raw)
    persist_observations(
        observations,
        seed_history=data_source == "mock",
        collectors=collectors,
    )
    group_key = select_primary_group(observations, query)
    if not group_key:
        return {
            "query": query,
            "observations": [],
            "analysis": None,
            "groups": [],
            "message": "No comparable products were collected. Try a catalog product such as 'Sony WH-1000XM5' in Demo mode.",
        }
    analysis = analyze_group(group_key)
    groups = sorted({obs.group_key for obs in observations if obs.group_key})
    return {
        "query": query,
        "observations": observations,
        "analysis": analysis,
        "groups": groups,
        "message": None,
    }
