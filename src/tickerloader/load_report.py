import csv
import io
import json
import logging
import os
from typing import Dict, List

import boto3

from .loader import (
    insert_upload_task, update_upload_task_status, insert_rows)

s3_client = boto3.client("s3")


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    # Resolve S3 location from event
    # The filename includes the current timestamp to ensure uniqueness and traceability. It has the format "stock_price_{source}_YYYY-MM-DD_HHMM.csv", where {source} is the data source e,g, "av" for Alpha Vantage, 
    # YYYY-MM-DD is the current date, and HHMM is the current time in hours and minutes.
    bucket, key = resolve_s3_location(event)
    data_source = key.split("_")[2]  # Assuming key is like 'stock_price_av_2026-02-28.csv'
    business_date = key.split("_")[-1].replace(".csv", "")  # Assuming filename is like 'stock_price_av_2026-02-28.csv'

    # Write an upload task record with status 'in_progress'
    upload_task_id = insert_upload_task(business_date, bucket, key, data_source, "IN_PROGRESS")
    inserted = 0
	
    try:
        # Download, parse, and insert data
        csv_content = read_csv_from_local(key) if os.environ.get("DEBUG") == "true" else download_csv_from_s3(bucket, key)
        rows = parse_rows(csv_content)
        inserted = insert_rows(rows, upload_task_id)

        # Update upload task record with final status
        rows_succeeded  = inserted
        rows_failed = len(rows) - inserted
        update_upload_task_status(upload_task_id, rows_succeeded, rows_failed, "DONE")

        result = {
        "status": "completed",
        "source_bucket": bucket,
        "source_key": key,
        "rows_parsed": len(rows),
        "rows_inserted": inserted,
    }

    except Exception as e:
        logger.error("Error processing upload task %d: %s", upload_task_id, str(e))
        update_upload_task_status(upload_task_id, 0, 0, "ERROR")

        result = {
            "status": "failed",
            "source_bucket": bucket,
            "source_key": key,
            "rows_parsed": len(rows),
            "rows_inserted": inserted,
        }

    logger.info("Load completed: %s", json.dumps(result))
    return result


def resolve_s3_location(event: Dict) -> tuple[str, str]:
    records = event.get("Records", []) if isinstance(event, dict) else []
    if records:
        first_record = records[0]
        s3_info = first_record.get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name")
        key = s3_info.get("object", {}).get("key")
        if bucket and key:
            return bucket, key

    bucket = os.environ.get("S3_BUCKET_NAME")
    key = os.environ.get("TICKER_FILE_KEY")
    if bucket and key:
        return bucket, key

    raise ValueError("Unable to resolve S3 location. Provide S3 event or set S3_BUCKET_NAME and TICKER_FILE_KEY.")


def download_csv_from_s3(bucket: str, key: str) -> str:
    logger.info("Downloading ticker file from s3://%s/%s", bucket, key)
    response = s3_client.get_object(Bucket=bucket, Key=key)
    logger.info("Successfully downloaded ticker file from s3://%s/%s", bucket, key)
    return response["Body"].read().decode("utf-8")

def read_csv_from_local(key: str) -> str:
    logger.info("Reading ticker file from local path: %s", key)
    with open(key, "r", encoding="utf-8") as file:
        return file.read()

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

def main():
    # For local testing, you can set environment variables or provide a sample event
    os.environ["DEBUG"] = "true"
    os.environ["TICKER_FILE_KEY"] = "sample_ticker_data.csv"  # Ensure this file exists locally for testing

    sample_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "dummy-bucket"},
                    "object": {"key": "sample_ticker_data.csv"}
                }
            }
        ]
    }

    result = lambda_handler(sample_event, None)
    print(json.dumps(result, indent=2))
    
