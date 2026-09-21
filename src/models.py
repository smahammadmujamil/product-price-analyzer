"""SQLAlchemy persistence models and Pydantic transfer objects."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base. Engine-agnostic for SQLite or PostgreSQL."""


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("platform", "product_url", name="uq_products_platform_url"),
        Index("ix_products_platform", "platform"),
        Index("ix_products_name", "product_name"),
        Index("ix_products_group_key", "group_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(512), nullable=False)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    product_url: Mapped[str] = mapped_column(Text, nullable=False)
    seller: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    availability: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    group_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    data_origin: Mapped[str] = mapped_column(String(32), default="synthetic", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="PriceHistory.recorded_at",
    )


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        Index("ix_price_history_product_id", "product_id"),
        Index("ix_price_history_recorded_at", "recorded_at"),
        Index("ix_price_history_product_recorded", "product_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    mrp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    discount_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product: Mapped["Product"] = relationship(back_populates="price_history")


class ProductObservation(BaseModel):
    """Normalized snapshot produced by collectors after cleaning."""

    model_config = ConfigDict(str_strip_whitespace=True)

    product_name: str
    platform: str
    product_url: str
    current_price: float = Field(gt=0)
    original_price: Optional[float] = Field(default=None, gt=0)
    discount_percentage: Optional[float] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    review_count: Optional[int] = Field(default=None, ge=0)
    seller: Optional[str] = None
    availability: Optional[str] = None
    image_url: Optional[str] = None
    currency: str = "INR"
    data_origin: str = "synthetic"
    group_key: Optional[str] = None
    observed_at: Optional[datetime] = None

    @field_validator("product_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        HttpUrl(value)
        return value
