import os
import logging
import psycopg2
from datetime import date

# This module provides functions to manage upload tasks in the database, including inserting new tasks and updating their 
# status. The upload task records the business date, source bucket, source key, row count, row inserted and status of the
# upload process. The status can be 'IN_PROGRESS', 'DONE', or 'ERROR'.

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def _connect_to_db():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
        sslmode=os.environ.get("DB_SSLMODE", "require")
    )

def new_upload_task(business_date: date, bucket: str, key: str) -> int:
    """
    Inserts a new upload task record into the database with the provided business date, S3 bucket, S3 key, and data source.
    The initial status of the task is set to 'IN_PROGRESS'. Returns the ID of the newly created upload task.
    """
    return insert_upload_task(business_date, bucket, key, "IN_PROGRESS")

def complete_upload_task(upload_task_id: int, row_count: int, rows_inserted: int) -> int:
    """
    Updates the status of an existing upload task to 'DONE' and records the number of rows processed and inserted.
    Returns the number of affected rows in the database.
    """
    return update_upload_task_status(upload_task_id, row_count, rows_inserted, "DONE")

def fail_upload_task(upload_task_id: int, error_message: str = "") -> int:
    """
    Updates the status of an existing upload task to 'ERROR'. Returns the number of affected rows in the database.
    """
    return update_upload_task_status(upload_task_id, 0, 0, "ERROR", error_message)

# Inserts a new upload task record into the database and returns the generated task ID. The task is initialized with the provided business date, source bucket, source key, and status.
def insert_upload_task(business_date: date, source_bucket: str, source_key: str, status: str) -> int:
    schema_name = os.environ.get("DB_SCHEMA", "market_data")
    insert_sql = f"""
		INSERT INTO {schema_name}.upload_task (
			business_date,
			s3_bucket,
			s3_key,
			row_count,
			rows_inserted,
			status
		)
		VALUES (%s, %s, %s, %s, %s, %s)
		RETURNING task_id
	"""

    with _connect_to_db() as connection:
        with connection.cursor() as cursor:            
            cursor.execute(
                insert_sql,
                (business_date, source_bucket, source_key, 0, 0, status),
            )
            record = cursor.fetchone()
            if record is None:
                raise RuntimeError("INSERT returned no id — row may not have been inserted")
            return int(record[0])

# Updates the status and row counts of an existing upload task. Returns the number of affected rows in the database.
def update_upload_task_status(upload_task_id: int, row_count: int, rows_inserted: int, status: str, error_message: str = "") -> int:
    schema_name = os.environ.get("DB_SCHEMA", "market_data")
    update_sql = f"""
		UPDATE {schema_name}.upload_task
		SET status = %s, row_count = %s, rows_inserted = %s, error_message = %s, last_updated_at = CURRENT_TIMESTAMP
		WHERE task_id = %s
	"""

    with _connect_to_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(update_sql, (status, row_count, rows_inserted, error_message, upload_task_id))
            return cursor.rowcount
