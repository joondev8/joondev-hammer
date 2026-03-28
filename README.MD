# Joondev Hammer

Python project for daily stock ticker reporting:
- `tickercollector` generates OHLC CSV files and uploads them to S3.
- `tickerloader` reads CSV files from S3 and loads rows into PostgreSQL on AWS RDS.
- `main.py` exposes a FastAPI service for triggering loads via HTTP.

## Overview

The repository contains two flows and a REST API:

1. **Generate + upload flow** (AWS Lambda)
   - Builds CSV content for configured tickers using Alpha Vantage (`requests`)
   - Uploads generated content to S3 (`boto3`)

2. **Load flow** (AWS ECS)
   - Resolves S3 location from EventBridge or S3 notification event records, or environment-variable fallback
   - Downloads and parses CSV rows
   - Inserts data into `market_data.raw_ticker_prices`
   - Tracks load status in `market_data.upload_task` (`IN_PROGRESS` → `DONE` / `ERROR`), including `rows_succeeded` and `rows_failed`

3. **REST API** (FastAPI / Docker)
   - `GET /health` — liveness check
   - `POST /ticker-files/{filename}/load` — triggers a load from S3 for the given file

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
│   ├── main.tf
│   ├── scheduler.tf
│   ├── terraform.tfvars
│   ├── variables.tf
│   └── ecs/
│       ├── iam.tf
│       ├── main.tf
│       ├── security.tf
│       ├── terraform.tfvars
│       └── variables.tf
├── tests/
│   ├── test_generator.py
│   ├── test_loader.py
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
- `S3_BUCKET_NAME` and `TICKER_FILE_KEY` (optional fallback when event has no S3 record)
- `DB_HOST` (required): RDS endpoint
- `DB_PORT` (optional): database port, default `5432`
- `DB_NAME` (required): PostgreSQL database name
- `DB_USERNAME` (required): database username
- `DB_PASSWORD` (required): database password
- `DB_SCHEMA` (optional): schema name, default `market_data`
- `DB_SSLMODE` (optional): SSL mode, default `require`
- `DEBUG` (optional): set to `"true"` to read CSV from local file path in `TICKER_FILE_KEY`

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

### Lambda handler

- Generator/upload: `tickercollector.generate_report.lambda_handler`

### Local invocation example (generator)

```python
from tickercollector.generate_report import lambda_handler

result = lambda_handler({}, None)
print(result)
```

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
python -m tickerloader
```

If you run from repository root, set `PYTHONPATH=src` first (or use the VS Code launch profile already configured).

## Known assumptions

- `tickerloader.load_report.load_report_to_db` derives `data_source` from `key.split("_")[2]`.
- It derives `business_date` from the filename portion of the key (`key.split("_")[-1]`, without `.csv`).
- Expected key format for correct metadata extraction is `stock_price_{source}_YYYY-MM-DD.csv` (example: `stock_price_av_2026-02-28.csv`).
- Keys not matching this format may fail during metadata parsing (for example, `IndexError`) or produce incorrect `data_source` / `business_date` values in `upload_tasks`.

## Notes

- `pytest.ini` sets `pythonpath = src`, so imports use `tickercollector.*` and `tickerloader.*`.
- Loader row parsing expects CSV columns: `Date`, `Ticker`, `Open`, `High`, `Low`, `Close`.
- `db/001_create_ticker_prices.sql` defines the PostgreSQL schema used by loader persistence.
