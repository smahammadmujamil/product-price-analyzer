"""Database CRUD tests against an isolated SQLite file."""

from datetime import datetime, timedelta, timezone

from src.database import (
    create_database,
    get_latest_prices,
    get_price_history,
    get_product,
    get_session,
    insert_price_history,
    insert_product,
    init_engine,
)
from src.models import Base


def test_product_and_price_history_roundtrip(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path.as_posix()}"
    engine = init_engine(url)
    Base.metadata.drop_all(engine)
    create_database(url)

    with get_session() as session:
        product = insert_product(
            session,
            {
                "product_name": "Sony WH-1000XM5 Wireless Headphones",
                "platform": "Amazon",
                "product_url": "https://www.amazon.in/dp/DEMOWH1000XM5",
                "seller": "Amazon Retail",
                "rating": 4.5,
                "review_count": 12400,
                "availability": "In Stock",
                "image_url": "https://placehold.co/400x400?text=Sony",
                "group_key": "sony-wh-1000-xm5-headphones",
                "currency": "INR",
                "data_origin": "synthetic",
            },
        )
        first_id = product.id
        insert_price_history(session, first_id, price=7999, mrp=29990, discount_percentage=73.33)
        insert_price_history(
            session,
            first_id,
            price=7499,
            mrp=29990,
            discount_percentage=75.0,
            recorded_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        )

        fetched = get_product(session, first_id)
        assert fetched is not None
        assert fetched.platform == "Amazon"
        history = get_price_history(session, first_id)
        assert len(history) == 2
        latest = get_latest_prices(session, group_key="sony-wh-1000-xm5-headphones")
        assert len(latest) == 1
        assert latest[0]["price"] == 7499

        updated = insert_product(
            session,
            {
                "product_name": "Sony WH-1000XM5 Wireless Headphones",
                "platform": "Amazon",
                "product_url": "https://www.amazon.in/dp/DEMOWH1000XM5",
                "seller": "Amazon Retail",
                "rating": 4.6,
                "review_count": 13000,
                "availability": "In Stock",
                "image_url": "https://placehold.co/400x400?text=Sony",
                "group_key": "sony-wh-1000-xm5-headphones",
                "currency": "INR",
                "data_origin": "synthetic",
            },
        )
        assert updated.id == first_id
        assert updated.rating == 4.6
