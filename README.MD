# Joondev Hammer

Serverless Python project for daily stock ticker reporting:
- `dailyticker` generates OHLC CSV files and uploads them to S3.
- `tickerloader` reads CSV files from S3 and loads rows into SQLite.

## Overview

The repository currently contains two AWS Lambda-oriented flows:

1. **Generate + upload flow**
   - Builds CSV content for configured tickers using Alpha Vantage (`requests`)
   - Uploads the file to an S3 bucket (`boto3`)

2. **Load flow**
   - Resolves an S3 object location from event data or environment variables
   - Downloads and parses CSV rows
   - Inserts row data into SQLite (`stock_prices`)
   - Tracks loader task state in `upload_tasks`

## Project Structure

```
joondev-hammer/
├── src/
│   ├── dailyticker/
│   │   ├── generate_report.py
│   │   ├── generator.py
│   │   └── uploader.py
│   └── tickerloader/
│       ├── __init__.py
│       ├── load_report.py
│       └── loader.py
├── db/
│   └── 001_create_ticker_prices.sql
├── terraform/
│   ├── main.tf
│   ├── notifications.tf
│   ├── scheduler.tf
│   ├── terraform.tfvars
│   └── variables.tf
├── tests/
│   ├── test_generator.py
│   └── test_uploader.py
├── requirements.txt
└── pytest.ini
```

## Requirements

- Python 3.12
- AWS account + permissions for S3/Lambda (for cloud execution)
- Terraform (optional, for infra provisioning)

## Install

```bash
pip install -r requirements.txt
```

## Environment Variables

### `dailyticker`
- `S3_BUCKET_NAME` (required): destination S3 bucket for generated reports
- `AV_API_KEY` (optional): Alpha Vantage API key; when missing, report values fallback to `N/A`

### `tickerloader`
- `S3_BUCKET_NAME` and `TICKER_FILE_KEY` (optional fallback when event has no S3 record)
- `SQLITE_DB_PATH` (optional): SQLite file path; defaults to `%TEMP%/tickerloader.db`

## Usage

### Run tests

```bash
pytest -v
```

### Lambda handlers

- Generator/upload handler: `app.dailyticker.generate_report.lambda_handler`
- Loader handler: `app.tickerloader.load_report.lambda_handler`

### Local invocation example (generator)

```python
from app.dailyticker.generate_report import lambda_handler

result = lambda_handler({}, None)
print(result)
```

### Local invocation example (loader)

```python
from app.tickerloader.load_report import lambda_handler

event = {
	"Records": [
		{
			"s3": {
				"bucket": {"name": "your-bucket"},
				"object": {"key": "2026-02-28.csv"}
			}
		}
	]
}

result = lambda_handler(event, None)
print(result)
```

## Notes

- Test coverage currently focuses on `dailyticker` generator and uploader behavior.
- The `db/001_create_ticker_prices.sql` file is PostgreSQL-oriented for infra/schema reference, while loader runtime persistence is currently SQLite.
