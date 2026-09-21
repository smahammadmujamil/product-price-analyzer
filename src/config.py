"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    value = value.strip()
    return value or None


class Settings:
    """Runtime settings. Secrets stay in environment variables, never in code."""

    app_name: str = "Product Price Analyzer"
    app_env: str = _env("APP_ENV", "development") or "development"
    log_level: str = (_env("LOG_LEVEL", "INFO") or "INFO").upper()
    database_url: str = (
        _env("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'price_analyzer.db').as_posix()}")
        or f"sqlite:///{(DATA_DIR / 'price_analyzer.db').as_posix()}"
    )
    data_source: str = (_env("DATA_SOURCE", "mock") or "mock").lower()
    request_timeout_seconds: int = int(_env("REQUEST_TIMEOUT_SECONDS", "10") or "10")
    request_delay_seconds: float = float(_env("REQUEST_DELAY_SECONDS", "2.0") or "2.0")
    user_agent: str = (
        _env("USER_AGENT", "ProductPriceAnalyzer/1.0 (portfolio project; educational use)")
        or "ProductPriceAnalyzer/1.0 (portfolio project; educational use)"
    )
    sample_products_path: Path = DATA_DIR / "sample_products.csv"
    currency: str = "INR"

    amazon_paapi_access_key: str | None = _env("AMAZON_PAAPI_ACCESS_KEY")
    amazon_paapi_secret_key: str | None = _env("AMAZON_PAAPI_SECRET_KEY")
    amazon_paapi_partner_tag: str | None = _env("AMAZON_PAAPI_PARTNER_TAG")
    amazon_paapi_host: str | None = _env("AMAZON_PAAPI_HOST", "webservices.amazon.in")
    amazon_paapi_region: str | None = _env("AMAZON_PAAPI_REGION", "eu-west-1")

    flipkart_affiliate_id: str | None = _env("FLIPKART_AFFILIATE_ID")
    flipkart_affiliate_token: str | None = _env("FLIPKART_AFFILIATE_TOKEN")

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def amazon_official_api_configured(self) -> bool:
        return bool(
            self.amazon_paapi_access_key
            and self.amazon_paapi_secret_key
            and self.amazon_paapi_partner_tag
        )

    @property
    def flipkart_official_api_configured(self) -> bool:
        return bool(self.flipkart_affiliate_id and self.flipkart_affiliate_token)


settings = Settings()
