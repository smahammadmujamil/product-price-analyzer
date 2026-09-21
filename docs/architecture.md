# Product Price Analyzer — Architecture

## Purpose

Product Price Analyzer is a modular price-intelligence application. Users search by product name or URL. Collectors return raw listings, processing code cleans and normalizes them, SQLAlchemy stores current and historical observations, and Streamlit presents comparison, history, and a recommendation.

The design goal is **marketplace independence**: Amazon and Flipkart are the first two sources. Additional sources plug in through the collector factory.

## Layered design

```text
app.py                         Streamlit UI only
src/pipeline.py                Orchestration
src/collectors/                Inbound adapters
src/processing/                Cleaning + normalization
src/analytics/                 Formulas, recommendations, charts
src/database.py + models.py    Persistence
src/config.py                  Environment configuration
```

`app.py` does not contain SQL, HTTP, or formula logic.

## Collector pattern

`BaseCollector` defines:

- `search_product(query)`
- `get_product_details(url)`

Implementations:

- `MockCollector` — synthetic catalog; always available
- `AmazonCollector` — official PA-API placeholder + polite public fetch that fails closed
- `FlipkartCollector` — affiliate API when configured + polite public fetch that fails closed

`CollectorFactory.default_collectors(data_source)` injects the active collectors. Register new classes in `COLLECTOR_REGISTRY` without changing the pipeline:

```text
MyntraCollector
CromaCollector
RelianceDigitalCollector
```

Access policy:

- Respect robots.txt
- Honor delays and timeouts
- Do not solve CAPTCHA or rotate identities to evade controls
- Treat 401/403/429 as a stop condition
- Label synthetic rows as `data_origin=synthetic`

## Data model

### products

| Column | Role |
| --- | --- |
| id | Primary key |
| product_name | Display name |
| platform | Amazon, Flipkart, … |
| product_url | Unique with platform |
| seller, rating, review_count, availability, image_url | Listing attributes |
| group_key | Cross-platform match key |
| currency, data_origin | Context |
| created_at, updated_at | Audit |

Unique constraint: `(platform, product_url)`

### price_history

| Column | Role |
| --- | --- |
| id | Primary key |
| product_id | Foreign key → products.id |
| price, mrp, discount_percentage | Observation |
| recorded_at | When the price was seen |

Indexes support latest-price lookup and time-series charts.

SQLite is the default engine. `DATABASE_URL` can point at PostgreSQL later; models use SQLAlchemy 2.0 types rather than SQLite-only SQL.

## Processing

Cleaning (`src/processing/cleaner.py`):

- `₹7,499` → `7499.0`
- `4.3 out of 5` → `4.3`
- `2.4K` → `2400`
- Invalid prices, ratings, URLs, and empty names are dropped

Normalization (`src/processing/normalizer.py`):

- Platform aliases (`amazon.in` → `Amazon`)
- Product-name whitespace and punctuation
- `group_key` from significant tokens so Amazon/Flipkart listings of the same product can be compared
- Duplicate `(platform, url)` rows removed

Validated snapshots are Pydantic `ProductObservation` objects.

## Analysis formulas

Price difference:

```text
Amazon price − Flipkart price
```

Percentage difference (default reference = mean of the two prices):

```text
(Amazon − Flipkart) / ((Amazon + Flipkart) / 2) × 100
```

Discount:

```text
(MRP − current price) / MRP × 100
```

Historical statistics per platform:

```text
current              = last observation
min / max / average  = over stored history
price_change         = current − previous
change %             = (current − previous) / previous × 100
volatility           = sample_stdev(prices) / mean(prices)
```

Recommendations apply explicit rules in `src/analytics/recommendations.py` (near historical low → buy now; well above average → wait; otherwise prefer the cheapest in-stock platform).

## Dashboard

Streamlit page `app.py`:

1. Search box and data-source toggle
2. Origin banner (synthetic vs live)
3. KPI cards
4. Recommendation
5. Comparison table
6. Plotly current-price bar and historical line chart
7. Formula expander

## Testing

| File | Scope |
| --- | --- |
| `tests/test_cleaner.py` | Currency, ratings, reviews, URLs, duplicates |
| `tests/test_price_analysis.py` | Formulas and recommendation rules |
| `tests/test_database.py` | Insert/get product and price history |

## Future work

- Signed Amazon Product Advertising API client when the caller has a partner tag
- PostgreSQL + scheduled observation jobs
- Stronger product matching (brand/model attributes, embeddings)
- Export of comparison CSVs
