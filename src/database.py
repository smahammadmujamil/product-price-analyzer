"""Database session management and CRUD. Engine is selected via DATABASE_URL."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import create_engine, desc, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings
from src.models import Base, PriceHistory, Product
from src.utils.logger import get_logger

logger = get_logger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or settings.database_url
    connect_args: dict[str, Any] = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, future=True, echo=False, connect_args=connect_args)


def init_engine(database_url: str | None = None) -> Engine:
    global _engine, _SessionLocal
    _engine = get_engine(database_url)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def create_database(database_url: str | None = None) -> None:
    """Create tables if they do not exist."""
    engine = init_engine(database_url)
    Base.metadata.create_all(engine)
    logger.info("Database tables ensured for %s", database_url or settings.database_url)


@contextmanager
def get_session(database_url: str | None = None) -> Generator[Session, None, None]:
    if database_url is not None:
        engine = get_engine(database_url)
        factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        session = factory()
    else:
        if _SessionLocal is None:
            create_database()
        assert _SessionLocal is not None
        session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def insert_product(session: Session, data: dict[str, Any]) -> Product:
    """Insert or update a product keyed by platform + URL."""
    existing = session.scalar(
        select(Product).where(
            Product.platform == data["platform"],
            Product.product_url == data["product_url"],
        )
    )
    fields = {
        "product_name": data["product_name"],
        "platform": data["platform"],
        "product_url": data["product_url"],
        "seller": data.get("seller"),
        "rating": data.get("rating"),
        "review_count": data.get("review_count"),
        "availability": data.get("availability"),
        "image_url": data.get("image_url"),
        "group_key": data.get("group_key"),
        "currency": data.get("currency", "INR"),
        "data_origin": data.get("data_origin", "synthetic"),
    }
    if existing:
        for key, value in fields.items():
            setattr(existing, key, value)
        session.flush()
        return existing

    product = Product(**fields)
    session.add(product)
    session.flush()
    return product


def insert_price_history(
    session: Session,
    product_id: int,
    price: float,
    mrp: float | None = None,
    discount_percentage: float | None = None,
    recorded_at: datetime | None = None,
) -> PriceHistory:
    row = PriceHistory(
        product_id=product_id,
        price=price,
        mrp=mrp,
        discount_percentage=discount_percentage,
        recorded_at=recorded_at or datetime.now(timezone.utc),
    )
    session.add(row)
    session.flush()
    return row


def get_product(session: Session, product_id: int) -> Product | None:
    return session.get(Product, product_id)


def get_products_by_group(session: Session, group_key: str) -> list[Product]:
    return list(
        session.scalars(select(Product).where(Product.group_key == group_key)).all()
    )


def get_latest_prices(session: Session, group_key: str | None = None) -> list[dict[str, Any]]:
    """Return each product with its most recent price observation."""
    latest_subq = (
        select(
            PriceHistory.product_id.label("product_id"),
            func.max(PriceHistory.id).label("max_id"),
        )
        .group_by(PriceHistory.product_id)
        .subquery()
    )
    stmt = (
        select(Product, PriceHistory)
        .join(latest_subq, Product.id == latest_subq.c.product_id)
        .join(
            PriceHistory,
            PriceHistory.id == latest_subq.c.max_id,
        )
        .order_by(Product.platform)
    )
    if group_key:
        stmt = stmt.where(Product.group_key == group_key)

    rows: list[dict[str, Any]] = []
    for product, history in session.execute(stmt):
        rows.append(
            {
                "product_id": product.id,
                "product_name": product.product_name,
                "platform": product.platform,
                "product_url": product.product_url,
                "seller": product.seller,
                "rating": product.rating,
                "review_count": product.review_count,
                "availability": product.availability,
                "image_url": product.image_url,
                "group_key": product.group_key,
                "currency": product.currency,
                "data_origin": product.data_origin,
                "price": history.price,
                "mrp": history.mrp,
                "discount_percentage": history.discount_percentage,
                "recorded_at": history.recorded_at,
            }
        )
    return rows


def get_price_history(session: Session, product_id: int) -> list[PriceHistory]:
    return list(
        session.scalars(
            select(PriceHistory)
            .where(PriceHistory.product_id == product_id)
            .order_by(PriceHistory.recorded_at)
        ).all()
    )


def get_price_history_for_group(session: Session, group_key: str) -> list[dict[str, Any]]:
    stmt = (
        select(Product, PriceHistory)
        .join(PriceHistory, PriceHistory.product_id == Product.id)
        .where(Product.group_key == group_key)
        .order_by(PriceHistory.recorded_at, Product.platform)
    )
    results: list[dict[str, Any]] = []
    for product, history in session.execute(stmt):
        results.append(
            {
                "product_id": product.id,
                "product_name": product.product_name,
                "platform": product.platform,
                "price": history.price,
                "mrp": history.mrp,
                "discount_percentage": history.discount_percentage,
                "recorded_at": history.recorded_at,
                "currency": product.currency,
                "data_origin": product.data_origin,
            }
        )
    return results


def search_stored_products(session: Session, query: str, limit: int = 50) -> list[Product]:
    like = f"%{query.strip()}%"
    stmt = (
        select(Product)
        .where(Product.product_name.ilike(like))
        .order_by(desc(Product.updated_at))
        .limit(limit)
    )
    return list(session.scalars(stmt).all())
