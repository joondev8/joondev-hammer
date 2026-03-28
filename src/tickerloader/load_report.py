import json
import logging
import os
import sys
from typing import Dict

from tickerloader.loader import load_report_to_db as _load_report_to_db


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def load_report_to_db(event, context):
    bucket, key = resolve_s3_location(event)
    result = _load_report_to_db(bucket, key)
    logger.info("Load completed: %s", json.dumps(result))
    return result

def resolve_s3_location(event: Dict) -> tuple[str, str]:
    # EventBridge S3 event shape
    detail = event.get("detail", {})
    if detail:
        bucket = detail.get("bucket", {}).get("name")
        key = detail.get("object", {}).get("key")
        if bucket and key:
            return bucket, key

    # Lambda S3 notification shape
    records = event.get("Records", [])
    if records:
        s3_info = records[0].get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name")
        key = s3_info.get("object", {}).get("key")
        if bucket and key:
            return bucket, key

    raise ValueError("Unable to resolve S3 location. Event structure may be invalid or missing required information.")

def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    bucket = os.environ.get("S3_BUCKET_NAME")
    key = os.environ.get("S3_OBJECT_KEY")
    if not bucket or not key:
        logger.error("S3_BUCKET_NAME and S3_OBJECT_KEY environment variables must be set")
        sys.exit(1)

    result = _load_report_to_db(bucket, key)
    logger.info("Load completed: %s", json.dumps(result))

if __name__ == "__main__":
    main()
