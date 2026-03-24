import csv
import io
import json
import logging
import os
from typing import Dict, List

import boto3
import psycopg2

from tickerloader.task_manager import complete_upload_task, fail_upload_task, new_upload_task
from datetime import datetime


logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

def _connect_to_db():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
        sslmode=os.environ.get("DB_SSLMODE", "require")
    )

def download_csv_from_s3(bucket: str, key: str) -> str:
    logger.info("Downloading ticker file from s3://%s/%s", bucket, key)
    response = s3_client.get_object(Bucket=bucket, Key=key)
    logger.info("Successfully downloaded ticker file from s3://%s/%s", bucket, key)
    return response["Body"].read().decode("utf-8")

# This module provides functions to load ticker prices into the database. It downloads CSV files from S3, 
# parses the data, and inserts it into the database.
def load_report_to_db(bucket: str, filename: str):
    business_date = filename.split("_")[-2]  # Assuming filename is like 'stock_price_av_2026-03-09_2200.csv'    
    # Write an upload task record with status 'in_progress'
    business_date_obj = datetime.strptime(business_date, "%Y-%m-%d").date()
    upload_task_id = new_upload_task(business_date_obj, bucket, filename)

    try:
        if not bucket:
            raise ValueError("Variable 'bucket' is not set")

        logger.info("Starting to load report from s3://%s/%s", bucket, filename)

        csv_content = download_csv_from_s3(bucket, filename)
        rows = parse_rows(csv_content)
        inserted_count = insert_rows(rows, upload_task_id)

        complete_upload_task(upload_task_id, len(rows), inserted_count)
        logger.info("Successfully loaded report from s3://%s/%s. Rows inserted: %d", bucket, filename, inserted_count)
        return {
            "status": "success",
            "source_bucket": bucket,
            "source_key": filename,
            "rows_parsed": len(rows),
            "rows_inserted": inserted_count,
        }

    except Exception as e:
        fail_upload_task(upload_task_id, str(e))
        logger.error("Error loading report from s3://%s/%s: %s", bucket, filename, str(e))
        return {
            "status": "failed",
            "source_bucket": bucket,
            "source_key": filename,
            "error": str(e),
        }

def parse_rows(csv_content: str) -> List[Dict]:
    logger.info("Parsing ticker file content")
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = []

    for row in reader:
        rows.append(
            {
                "business_date": row.get("Date"),
                "ticker": row.get("Ticker"),
                "open_price": row.get("Open"),
                "high_price": row.get("High"),
                "low_price": row.get("Low"),
                "close_price": row.get("Close"),
            }
        )

    return rows

# insert rows into a table named 'raw_ticker_prices' with columns: date, ticker, open, high, low, close, upload_task_id
#
# Here is an example of how the input rows might look:
def insert_rows(rows: List[Dict], upload_task_id: int) -> int:
    if not rows:
        return 0

    schema_name = os.environ.get("DB_SCHEMA", "market_data")
    insert_sql = f"""
		INSERT INTO {schema_name}.raw_ticker_prices (
			business_date,
			ticker,
			open_price,
			high_price,
			low_price,
			close_price,
			upload_task_id
		)
		VALUES (%s, %s, %s, %s, %s, %s, %s)
	"""

    normalized_rows = []
    for row in rows:
        date_value = row.get("business_date") or row.get("date") or row.get("Date")
        ticker_value = row.get("ticker") or row.get("Ticker")
        open_value = row.get("open_price") or row.get("open") or row.get("Open")
        high_value = row.get("high_price") or row.get("high") or row.get("High")
        low_value = row.get("low_price") or row.get("low") or row.get("Low")
        close_value = row.get("close_price") or row.get("close") or row.get("Close")

        if not all([date_value, ticker_value, open_value, high_value, low_value, close_value]):
            logger.warning("Skipping row due to missing required values: %s", row)
            continue

        numeric_values = [open_value, high_value, low_value, close_value]
        if any(str(value).strip().upper() == "NA" for value in numeric_values):
            logger.warning("Skipping row due to NA numeric value: %s", row)
            continue

        try:
            open_float = float(open_value)
            high_float = float(high_value)
            low_float = float(low_value)
            close_float = float(close_value)
        except (TypeError, ValueError):
            logger.warning("Skipping row due to invalid numeric value: %s", row)
            continue

        normalized_rows.append(
            (
                str(date_value),
                str(ticker_value),
                open_float,
                high_float,
                low_float,
                close_float,
                upload_task_id,
            )
        )

    if not normalized_rows:
        return 0

    with _connect_to_db() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(insert_sql, normalized_rows)
            return cursor.rowcount

def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    bucket = os.getenv("S3_BUCKET_NAME")
    filename = "stock_price_av_2026-03-09_2200.csv"  # Example filename, replace with actual key in S3
    
    result = load_report_to_db(bucket, filename)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()