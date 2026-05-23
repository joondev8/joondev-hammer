# Joondev Hammer

Python ETL application for daily stock ticker reporting:
- `tickercollector` fetches OHLC data from Alpha Vantage, generates a CSV report, and uploads it to S3.
- `tickerloader` downloads the CSV from S3 and loads the rows into PostgreSQL on AWS RDS.

Both components run as short-lived AWS ECS Fargate tasks from a single Docker image.

## Architecture

```
EventBridge Scheduler (8pm ET, Mon–Fri)
        │
        ▼
ECS Fargate Task: tickercollector
  - Fetches OHLC data from Alpha Vantage for configured tickers
  - Generates CSV: eod_price_{source}_{business_date}_{timestamp}.csv
  - Uploads CSV to S3
        │
        ▼ (S3 Object Created event → EventBridge rule)
        │
        ▼
ECS Fargate Task: tickerloader
  - Downloads CSV from S3
  - Parses rows
  - Inserts into market_data.raw_ticker_prices (PostgreSQL / RDS)
  - Tracks status in market_data.upload_task (IN_PROGRESS → DONE / ERROR)
```

## Tickers

`AAPL`, `GOOGL`, `MSFT`, `AMZN`, `TSLA`, `TD.TO`, `SHOP.TO`

## Filename Format

Generated files follow the pattern:

```
eod_price_{source}_{business_date}_{timestamp}.csv
```

Example: `eod_price_av_20260509_20260509_2000.csv`

- `{source}` — data source identifier (e.g. `av` for Alpha Vantage)
- `{business_date}` — most recent US business day in `YYYYMMDD` format
- `{timestamp}` — run timestamp in `YYYYMMDD_HHMM` format

## Project Structure

```
joondev-hammer/
├── src/
│   ├── tickercollector/
│   │   ├── generate_report.py   # Entry point: fetches + uploads report
│   │   ├── generator.py         # Alpha Vantage API, CSV generation, business date logic
│   │   └── uploader.py          # S3 upload
│   └── tickerloader/
│       ├── load_report.py       # Entry point: resolves S3 location, triggers load
│       ├── loader.py            # S3 download, CSV parsing, DB insert
│       ├── task_manager.py      # upload_task lifecycle (IN_PROGRESS / DONE / ERROR)
│       └── db.py                # PostgreSQL connection pool (IAM or password auth)
├── db/
│   └── 001_create_ticker_prices.sql   # Schema: market_data.upload_task + raw_ticker_prices
├── terraform/
│   └── ecs/
│       ├── main.tf              # ECS cluster, task definitions, S3 bucket, EventBridge rule
│       ├── scheduler.tf         # EventBridge Scheduler (weekday cron)
│       ├── iam.tf               # IAM roles for tasks, exec, EventBridge, scheduler
│       ├── security.tf          # Security groups
│       ├── variables.tf
│       ├── terraform.tfvars
│       └── backend.hcl
├── tests/
│   ├── test_generator.py
│   ├── test_load_report.py
│   ├── test_loader.py
│   ├── test_task_manager.py
│   └── test_uploader.py
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

## Database Schema

Defined in `db/001_create_ticker_prices.sql`:

- **`market_data.upload_task`** — one record per file load, tracks status (`IN_PROGRESS` / `DONE` / `ERROR`), `row_count`, `rows_inserted`, `error_message`
- **`market_data.raw_ticker_prices`** — OHLC price rows with `business_date`, `ticker`, `open_price`, `high_price`, `low_price`, `close_price`, linked to `upload_task` via FK

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/) (dependency manager)
- Docker (for building the ECS image)
- AWS account with permissions for S3, ECS, ECR, EventBridge, RDS
- Terraform (for infrastructure provisioning)

## Install

```bash
uv sync
```

## Environment Variables

### `tickercollector`
| Variable | Required | Description |
|---|---|---|
| `S3_BUCKET_NAME` | Yes | Destination S3 bucket for generated reports |
| `AV_API_KEY` | No | Alpha Vantage API key; values fall back to `N/A` if not set |

### `tickerloader`
| Variable | Required | Description |
|---|---|---|
| `S3_BUCKET_NAME` | Yes | S3 bucket to read reports from |
| `S3_OBJECT_KEY` | Yes (CLI) | S3 key of the file to load (local/CLI mode only) |
| `DB_HOST` | Yes | RDS endpoint |
| `DB_PORT` | No | Database port, default `5432` |
| `DB_NAME` | Yes | PostgreSQL database name |
| `DB_USERNAME` | Yes | Database username |
| `DB_PASSWORD` | Yes (`password` mode) | Database password |
| `DB_SCHEMA` | No | Schema name, default `market_data` |
| `DB_SSLMODE` | No | SSL mode, default `require` (forced to `verify-full` for IAM auth) |
| `DB_AUTH_MODE` | No | `password` (default) or `iam` |
| `AWS_REGION` | Yes (IAM mode) | Used to generate the RDS IAM auth token |
| `DB_POOL_MAX_CONN` | No | Connection pool size, default `5` |

## Usage

### Run tests

```bash
uv run pytest -v
```

### Run collector locally

```bash
export S3_BUCKET_NAME=your-bucket
export AV_API_KEY=your-key
uv run python -m tickercollector.generate_report
```

### Run loader locally

```bash
export S3_BUCKET_NAME=your-bucket
export S3_OBJECT_KEY=eod_price_av_20260509_20260509_2000.csv
export DB_HOST=... DB_NAME=... DB_USERNAME=... DB_PASSWORD=...
uv run python -m tickerloader.load_report
```

### Build and push Docker image

```bash
docker build -t hammer-service .
docker tag hammer-service:latest <ecr-uri>/hammer-service:latest
docker push <ecr-uri>/hammer-service:latest
```

### Deploy infrastructure

```bash
cd terraform/ecs
terraform init -backend-config=backend.hcl
terraform apply -var-file=terraform.tfvars
```

## Notes

- `pyproject.toml` sets `pythonpath = ["src"]` under `[tool.pytest.ini_options]`, so test imports use `tickercollector.*` and `tickerloader.*`.
- `get_business_date()` rolls back to the most recent US business day, skipping weekends and US federal holidays (`holidays.US()`).
- `resolve_s3_location()` supports both EventBridge S3 Object Created events and S3 notification event shapes.
- Loader skips rows where any numeric field is `N/A` or non-numeric.
