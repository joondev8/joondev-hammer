# Joondev Hammer

Python project for daily stock ticker reporting with two standalone scripts:
- `tickercollector` fetches OHLC prices from Alpha Vantage and uploads a CSV to S3.
- `tickerloader` downloads the CSV from S3 and loads the rows into PostgreSQL on AWS RDS.

## Overview

### 1. Generate + upload (`tickercollector`)

Fetches daily OHLC data for a fixed list of tickers — `AAPL`, `GOOGL`, `MSFT`, `AMZN`, `TSLA`, `TD.TO`, `SHOP.TO` — via the Alpha Vantage API and writes a CSV to S3.

- `generator.py` — builds the CSV in memory; falls back to `N/A` values when no API key is set or the rate limit is hit
- `uploader.py` — uploads the CSV content to S3 using `boto3`
- `generate_report.py` — entry point; reads `S3_BUCKET_NAME` and calls the above two modules

CSV format: `Date, Ticker, Open, High, Low, Close, Volume`  
Filename format: `stock_price_av_YYYY-MM-DD_HHMM.csv`

### 2. Load to database (`tickerloader`)

Downloads a CSV from S3, parses each row, and inserts the data into PostgreSQL. Every run is tracked in an `upload_task` record.

- `loader.py` — downloads the CSV, parses rows, inserts into `market_data.raw_ticker_prices`, tracks status via `task_manager`
- `task_manager.py` — writes `upload_task` rows with status `IN_PROGRESS` → `DONE` / `ERROR`, recording `row_count`, `rows_inserted`, and `error_message`
- `db.py` — connection pool; supports password auth and IAM token auth (auto-refreshed on expiry)
- `load_report.py` — entry point; resolves the S3 bucket/key from an EventBridge or S3 notification event, then calls `loader`

The Docker image `CMD` runs this entry point directly:

```
CMD ["python", "-m", "tickerloader.load_report"]
```

## Project Structure

```
joondev-hammer/
├── src/
│   ├── tickercollector/
│   │   ├── __init__.py
│   │   ├── generate_report.py
│   │   ├── generator.py
│   │   └── uploader.py
│   └── tickerloader/
│       ├── __init__.py
│       ├── db.py
│       ├── load_report.py
│       ├── loader.py
│       └── task_manager.py
├── db/
│   └── 001_create_ticker_prices.sql
├── terraform/
│   └── ecs/
│       ├── iam.tf
│       ├── main.tf
│       ├── scheduler.tf
│       ├── security.tf
│       └── variables.tf
├── tests/
│   ├── test_generator.py
│   ├── test_load_report.py
│   ├── test_loader.py
│   ├── test_task_manager.py
│   └── test_uploader.py
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── requirements.txt
└── pytest.ini
```

## Requirements

- Python 3.12
- Docker (for containerised deployment)
- AWS account with permissions for S3 and ECS
- PostgreSQL on AWS RDS
- Terraform (optional, for infrastructure provisioning)

## Install

```bash
pip install -r requirements.txt
```

## Environment Variables

### `tickercollector`

| Variable | Required | Default | Description |
|---|---|---|---|
| `S3_BUCKET_NAME` | ✅ | — | Destination S3 bucket for generated CSV files |
| `AV_API_KEY` | ❌ | — | Alpha Vantage API key; rows fall back to `N/A` when unset |

### `tickerloader`

| Variable | Required | Default | Description |
|---|---|---|---|
| `S3_BUCKET_NAME` | ✅ | — | Source S3 bucket |
| `S3_OBJECT_KEY` | ✅ | — | Source S3 object key (CSV filename) |
| `DB_HOST` | ✅ | — | RDS endpoint |
| `DB_NAME` | ✅ | — | PostgreSQL database name |
| `DB_USERNAME` | ✅ | — | Database username |
| `DB_PASSWORD` | ✅* | — | Database password (*not used when `DB_AUTH_MODE=iam`) |
| `DB_PORT` | ❌ | `5432` | Database port |
| `DB_SCHEMA` | ❌ | `market_data` | PostgreSQL schema name |
| `DB_SSLMODE` | ❌ | `require` | SSL mode (forced to `verify-full` for IAM auth) |
| `DB_AUTH_MODE` | ❌ | `password` | Auth mode: `password` or `iam` |
| `AWS_REGION` | ✅ when IAM | — | AWS region used to generate the RDS IAM auth token |
| `DB_POOL_MAX_CONN` | ❌ | `5` | Connection pool size |

## Usage

### Run tests

```bash
pytest -v
```

### Run generator

```bash
cd src
python -m tickercollector.generate_report
```

Requires `S3_BUCKET_NAME` (and optionally `AV_API_KEY`) to be set.

### Run loader

```bash
cd src
python -m tickerloader.load_report
```

Requires `S3_BUCKET_NAME`, `S3_OBJECT_KEY`, and all `DB_*` variables to be set. From the repository root, prefix with `PYTHONPATH=src`.

### Run loader via Docker

```bash
docker compose up
```

The container runs `python -m tickerloader.load_report` by default (see `Dockerfile`).

### Local invocation example (loader)

```python
from tickerloader.load_report import load_report_to_db

event = {
    "Records": [
        {
            "s3": {
                "bucket": {"name": "your-bucket"},
                "object": {"key": "stock_price_av_2026-03-09_2200.csv"}
            }
        }
    ]
}

result = load_report_to_db(event, None)
print(result)
```

## Database Schema

Defined in `db/001_create_ticker_prices.sql`:

- **`market_data.upload_task`** — one row per load run; tracks `status` (`IN_PROGRESS` / `DONE` / `ERROR`), `row_count`, `rows_inserted`, and `error_message`
- **`market_data.raw_ticker_prices`** — one row per ticker per business date; columns: `business_date`, `ticker`, `open_price`, `high_price`, `low_price`, `close_price`, `upload_task_id`

## Notes

- `pytest.ini` sets `pythonpath = src`, so test imports use `tickercollector.*` and `tickerloader.*`.
- The loader derives `business_date` from the filename: `filename.split("_")[-2]`. Files must follow the pattern `stock_price_av_YYYY-MM-DD_HHMM.csv` for correct date parsing.
- The generator writes a `Volume` column in the CSV; the loader ignores it.
- `load_report.resolve_s3_location` accepts both EventBridge S3 event shapes and S3 notification event shapes (`Records[*].s3`).
