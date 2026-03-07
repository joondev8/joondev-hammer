import logging
import importlib
import os
from typing import Dict, List

import boto3
import psycopg2
from psycopg2 import Error


logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


def _connect_to_db():
	return psycopg2.connect(
		host=os.environ["DB_HOST"],
		port=int(os.environ.get("DB_PORT", "5432")),
		dbname=os.environ["DB_NAME"],
		user=os.environ["DB_USERNAME"],
		password=os.environ["DB_PASSWORD"],
		sslmode=os.environ.get("DB_SSLMODE", "require"),
	)


# insert rows into a table named 'raw_ticker_prices' with columns: date, ticker, open, high, low, close, upload_task_id
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

		normalized_rows.append(
			(
				str(date_value),
				str(ticker_value),
				float(open_value),
				float(high_value),
				float(low_value),
				float(close_value),
				upload_task_id,
			)
		)

	if not normalized_rows:
		return 0

	with _connect_to_db() as connection:
		with connection.cursor() as cursor:
			cursor.executemany(insert_sql, normalized_rows)
			return cursor.rowcount


# upload task has business_date, source_bucket, source_key, data_source, status
# status can be IN_PROGRESS, DONE, ERROR
def insert_upload_task(business_date: str, source_bucket: str, source_key: str, data_source: str, status: str) -> int:
	schema_name = os.environ.get("DB_SCHEMA", "market_data")
	insert_sql = f"""
		INSERT INTO {schema_name}.upload_task (
			business_date,
			data_source,
			file_name,
			rows_succeeded,
			rows_failed,
			status_code
		)
		VALUES (%s, %s, %s, %s, %s, %s)
		RETURNING id
	"""

	with _connect_to_db() as connection:
		with connection.cursor() as cursor:
			cursor.execute(
				insert_sql,
				(business_date, data_source.upper(), source_key, 0, 0, status),
			)
			record = cursor.fetchone()
			return int(record[0])

# update the status of an existing upload task record in the database and return the number of affected rows
def update_upload_task_status(upload_task_id: int, rows_succeeded: int, rows_failed: int, status: str) -> int:
	schema_name = os.environ.get("DB_SCHEMA", "market_data")
	update_sql = f"""
		UPDATE {schema_name}.upload_task
		SET status_code = %s, rows_succeeded = %s, rows_failed = %s, last_updated_at = CURRENT_TIMESTAMP
		WHERE id = %s
	"""

	with _connect_to_db() as connection:
		with connection.cursor() as cursor:
			cursor.execute(update_sql, (status, rows_succeeded, rows_failed, upload_task_id))
			return cursor.rowcount
