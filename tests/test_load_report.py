import os
from unittest.mock import MagicMock, patch

import pytest

from tickerloader import load_report


# --- resolve_s3_location ---

def test_resolve_s3_location_eventbridge_shape():
    event = {
        "detail": {
            "bucket": {"name": "my-bucket"},
            "object": {"key": "reports/file.csv"},
        }
    }
    bucket, key = load_report.resolve_s3_location(event)
    assert bucket == "my-bucket"
    assert key == "reports/file.csv"


def test_resolve_s3_location_lambda_s3_notification_shape():
    event = {
        "Records": [{
            "s3": {
                "bucket": {"name": "my-bucket"},
                "object": {"key": "reports/file.csv"},
            }
        }]
    }
    bucket, key = load_report.resolve_s3_location(event)
    assert bucket == "my-bucket"
    assert key == "reports/file.csv"


def test_resolve_s3_location_raises_on_unrecognised_event():
    with pytest.raises(ValueError, match="Unable to resolve S3 location"):
        load_report.resolve_s3_location({})


# --- load_report_to_db handler ---

def test_load_report_to_db_handler_calls_loader(monkeypatch):
    mock_load = MagicMock(return_value={"status": "success"})
    monkeypatch.setattr(load_report, "_load_report_to_db", mock_load)

    event = {
        "detail": {
            "bucket": {"name": "my-bucket"},
            "object": {"key": "reports/file.csv"},
        }
    }
    result = load_report.load_report_to_db(event, None)

    mock_load.assert_called_once_with("my-bucket", "reports/file.csv")
    assert result == {"status": "success"}


# --- main ---

def test_main_exits_when_env_vars_missing():
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("S3_BUCKET_NAME", None)
        os.environ.pop("S3_OBJECT_KEY", None)
        with pytest.raises(SystemExit) as exc_info:
            load_report.main()
    assert exc_info.value.code == 1


def test_main_calls_loader_with_env_vars(monkeypatch):
    mock_load = MagicMock(return_value={"status": "success"})
    monkeypatch.setattr(load_report, "_load_report_to_db", mock_load)
    monkeypatch.setenv("S3_BUCKET_NAME", "my-bucket")
    monkeypatch.setenv("S3_OBJECT_KEY", "reports/file.csv")

    load_report.main()

    mock_load.assert_called_once_with("my-bucket", "reports/file.csv")
