# Product Price Analyzer

**Compare, analyze, and track product prices across online marketplaces.**

GitHub repository name: `product-price-analyzer`

This is a portfolio web application that searches a product, collects comparable listings, cleans and normalizes the fields, stores historical price observations in SQL, and presents analysis in a Streamlit dashboard.

Demo mode uses a **synthetic catalog**. Those prices are never labeled as live Amazon or Flipkart data.

## What this project demonstrates

- Python 3.11+ application structure
- Pandas / NumPy analysis
- SQLAlchemy + SQLite (PostgreSQL-ready URL)
- Data cleaning and normalization
- Database design with keys, indexes, and history
- Plotly visualization
- Streamlit dashboard
- Collector factory for additional marketplaces
- pytest coverage for cleaning, analytics, and persistence

## Architecture at a glance

```text
User enters product
        ↓
Search / Product URL
        ↓
Data Collection (Mock, Amazon, Flipkart)
        ↓
Data Cleaning
        ↓
Data Normalization
        ↓
SQLite (products + price_history)
        ↓
Price Analysis + Historical stats
        ↓
Recommendation
        ↓
Interactive Dashboard
```

Details: [docs/architecture.md](docs/architecture.md)

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
pytest
streamlit run app.py
```

Open the app at `http://localhost:8501`.

Try queries such as:

- `Sony WH-1000XM5`
- `iPhone 15`
- `Galaxy S24`
- `Air Max`
- `Kindle`

## Data sources

| Mode | Behavior |
| --- | --- |
| **Demo (synthetic catalog)** | Always works. Uses `data/sample_products.csv` plus generated history. Banner states that data is synthetic. |
| **Live attempt** | Uses `AmazonCollector` and `FlipkartCollector`. Requests are delayed, identify a portfolio user-agent, and **stop if robots.txt, HTTP 401/403/429, or an access challenge appears**. There is no CAPTCHA solving, login bypass, cookie theft, or anti-bot evasion. |

Official partner APIs can be enabled later with environment variables in `.env`. Credentials are never hard-coded.

## Database

SQLite file: `data/price_analyzer.db` (created on first run).

Switch later by changing `DATABASE_URL`, for example:

```text
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/price_analyzer
```

Tables:

- `products` — listing identity, seller, rating, availability
- `price_history` — price, MRP, discount, timestamp

## Adding another marketplace

1. Subclass `BaseCollector` in `src/collectors/`.
2. Implement `search_product` and `get_product_details` using permitted APIs only.
3. Register the class in `COLLECTOR_REGISTRY` inside `src/collectors/factory.py`.

Examples of future collectors: `MyntraCollector`, `CromaCollector`, `RelianceDigitalCollector`.

## Tests

```bash
pytest
```

## License / ethics

Use this project for learning and portfolio demonstration. Do not use it to scrape behind logins, ignore robots.txt, or circumvent marketplace protections.
