# Joondev Hammer

Python project for daily stock ticker reporting:
- `tickercollector` generates OHLC CSV files and uploads them to S3.
- `tickerloader` reads CSV files from S3 and loads rows into PostgreSQL on AWS RDS.
- `main.py` exposes a FastAPI service for triggering loads via HTTP.

## Overview

The repository contains two flows and a REST API shell:

1. **Generate + upload flow** (standalone Python script)
   - Builds CSV content for configured tickers using Alpha Vantage (`requests`)
   - Uploads generated content to S3 (`boto3`)
   - Entry point: `python -m tickercollector.generate_report`

2. **Load flow** (AWS ECS)
   - Resolves S3 location from EventBridge or S3 notification event records
   - Downloads and parses CSV rows
   - Inserts data into `market_data.raw_ticker_prices`
   - Tracks load status in `market_data.upload_task` (`IN_PROGRESS` → `DONE` / `ERROR`), including `row_count`, `rows_inserted`, and `error_message`
   - Default container entry point: `python -m tickerloader.load_report`

3. **REST API** (FastAPI / Docker)
   - The FastAPI application is defined in `main.py` but all routes are currently commented out.
   - Previously planned endpoints: `GET /health` and `POST /ticker-files/{filename}/load`

## Project Structure

```
joondev-hammer/
├── src/
│   ├── main.py
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
- Docker (for containerised local development or production deployment)
- AWS account + permissions for S3/Lambda/ECS (for cloud execution)
- Terraform (optional, for infra provisioning)

## Install

```bash
pip install -r requirements.txt
```

## Environment Variables

### `tickercollector`
- `S3_BUCKET_NAME` (required): destination S3 bucket for generated reports
- `AV_API_KEY` (optional): Alpha Vantage API key; when missing, report values fall back to `N/A`

### `tickerloader` / API
- `S3_BUCKET_NAME` (required for the FastAPI endpoint and CLI mode)
- `S3_OBJECT_KEY` (required for CLI mode via `python -m tickerloader.load_report`)
- `DB_HOST` (required): RDS endpoint
- `DB_PORT` (optional): database port, default `5432`
- `DB_NAME` (required): PostgreSQL database name
- `DB_USERNAME` (required): database username
- `DB_PASSWORD` (required): database password
- `DB_SCHEMA` (optional): schema name, default `market_data`
- `DB_SSLMODE` (optional): SSL mode, default `require`
- `DB_AUTH_MODE` (optional): `password` (default) or `iam`
- `AWS_REGION` (required when `DB_AUTH_MODE=iam`): used to generate the RDS IAM auth token
- `DB_POOL_MAX_CONN` (optional): connection pool size, default `5`

## Usage

### Run tests

```bash
pytest -v
```

### Run API locally (Docker)

```bash
docker compose up
```

The API is available at `http://localhost:8010`.

### Run API locally (without Docker)

```bash
cd src
uvicorn main:app --reload --port 8010
```

### Run generator (standalone script)

```bash
cd src
python -m tickercollector.generate_report
```

Requires `S3_BUCKET_NAME` (and optionally `AV_API_KEY`) to be set.

### Lambda handler

> ⚠️ `tickercollector.generate_report.lambda_handler` is currently commented out. The generator runs as a standalone script (see above).

### Local invocation example (generator)

```python
from tickercollector.generate_report import main

main()
```

Requires `S3_BUCKET_NAME` to be set in your environment.

### Local invocation example (loader)

```python
from tickerloader.load_report import load_report_to_db

event = {
	"Records": [
		{
			"s3": {
				"bucket": {"name": "your-bucket"},
				"object": {"key": "stock_price_av_2026-02-28.csv"}
			}
		}
	]
}

result = load_report_to_db(event, None)
print(result)
```

### Package-mode local run (loader)

```bash
python -m tickerloader.load_report
```

If you run from repository root, set `PYTHONPATH=src` first. This is also the default `CMD` used by the Docker image.

## Known assumptions

- `tickerloader.loader.load_report_to_db` derives `business_date` from `filename.split("_")[-2]`.
- Expected key format for correct metadata extraction is `stock_price_{source}_YYYY-MM-DD_HHMM.csv` (example: `stock_price_av_2026-03-09_2200.csv`).
- Keys not matching this format may fail during metadata parsing or date conversion.

## Notes

- `pytest.ini` sets `pythonpath = src`, so imports use `tickercollector.*` and `tickerloader.*`.
- Loader row parsing expects CSV columns: `Date`, `Ticker`, `Open`, `High`, `Low`, `Close`.
- The generator currently writes an additional `Volume` column; the loader ignores it.
- `tickerloader.load_report.resolve_s3_location` supports EventBridge S3 events and S3 notification event shapes.
- `db/001_create_ticker_prices.sql` defines the PostgreSQL schema used by loader persistence.
- `main.py` defines a FastAPI application; all route handlers are currently commented out. The `docker-compose.yml` service still wires up `uvicorn main:app` for local development.
