import json
import logging
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
    records = event.get("Records", []) if isinstance(event, dict) else []
    if records:
        first_record = records[0]
        s3_info = first_record.get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name")
        key = s3_info.get("object", {}).get("key")
        if bucket and key:
            return bucket, key

    raise ValueError("Unable to resolve S3 location. Event structure may be invalid or missing required information.")
