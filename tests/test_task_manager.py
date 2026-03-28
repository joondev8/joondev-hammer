from datetime import date
from unittest.mock import MagicMock, call

import pytest

from tickerloader import task_manager


def _mock_db(monkeypatch, fetchone_value=None, rowcount=1):
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.__exit__.return_value = None

    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone_value
    cursor.rowcount = rowcount
    cursor.__enter__.return_value = cursor
    cursor.__exit__.return_value = None

    connection.cursor.return_value = cursor
    monkeypatch.setattr(task_manager, "get_connection", lambda: connection)
    return connection, cursor


# --- insert_upload_task ---

def test_insert_upload_task_returns_task_id(monkeypatch):
    _, cursor = _mock_db(monkeypatch, fetchone_value=(42,))

    task_id = task_manager.insert_upload_task(
        date(2026, 3, 9), "test-bucket", "stock_price_av_2026-03-09_2200.csv", "IN_PROGRESS"
    )

    assert task_id == 42
    cursor.execute.assert_called_once()
    args = cursor.execute.call_args.args[1]
    assert args == (date(2026, 3, 9), "test-bucket", "stock_price_av_2026-03-09_2200.csv", 0, 0, "IN_PROGRESS")


def test_insert_upload_task_raises_when_no_id_returned(monkeypatch):
    _mock_db(monkeypatch, fetchone_value=None)

    with pytest.raises(RuntimeError, match="INSERT returned no id"):
        task_manager.insert_upload_task(
            date(2026, 3, 9), "test-bucket", "stock_price_av_2026-03-09_2200.csv", "IN_PROGRESS"
        )


def test_insert_upload_task_uses_custom_schema(monkeypatch):
    monkeypatch.setenv("DB_SCHEMA", "custom_schema")
    _, cursor = _mock_db(monkeypatch, fetchone_value=(7,))

    task_manager.insert_upload_task(
        date(2026, 3, 9), "test-bucket", "stock_price_av_2026-03-09_2200.csv", "IN_PROGRESS"
    )

    sql = cursor.execute.call_args.args[0]
    assert "custom_schema.upload_task" in sql


# --- update_upload_task_status ---

def test_update_upload_task_status_returns_rowcount(monkeypatch):
    _, cursor = _mock_db(monkeypatch, rowcount=1)

    affected = task_manager.update_upload_task_status(42, 10, 8, "DONE")

    assert affected == 1
    cursor.execute.assert_called_once()
    args = cursor.execute.call_args.args[1]
    assert args == ("DONE", 10, 8, "", 42)


def test_update_upload_task_status_includes_error_message(monkeypatch):
    _, cursor = _mock_db(monkeypatch, rowcount=1)

    task_manager.update_upload_task_status(42, 0, 0, "ERROR", "something went wrong")

    args = cursor.execute.call_args.args[1]
    assert args == ("ERROR", 0, 0, "something went wrong", 42)


def test_update_upload_task_status_returns_zero_for_missing_task(monkeypatch):
    _, cursor = _mock_db(monkeypatch, rowcount=0)

    affected = task_manager.update_upload_task_status(9999, 0, 0, "ERROR")

    assert affected == 0


# --- new_upload_task ---

def test_new_upload_task_inserts_with_in_progress_status(monkeypatch):
    _, cursor = _mock_db(monkeypatch, fetchone_value=(5,))

    task_id = task_manager.new_upload_task(date(2026, 3, 9), "test-bucket", "stock_price_av_2026-03-09_2200.csv")

    assert task_id == 5
    args = cursor.execute.call_args.args[1]
    assert args[5] == "IN_PROGRESS"


# --- complete_upload_task ---

def test_complete_upload_task_sets_done_status(monkeypatch):
    _, cursor = _mock_db(monkeypatch, rowcount=1)

    affected = task_manager.complete_upload_task(10, 100, 98)

    assert affected == 1
    args = cursor.execute.call_args.args[1]
    assert args[0] == "DONE"
    assert args[1] == 100
    assert args[2] == 98


# --- fail_upload_task ---

def test_fail_upload_task_sets_error_status(monkeypatch):
    _, cursor = _mock_db(monkeypatch, rowcount=1)

    affected = task_manager.fail_upload_task(10, "connection timeout")

    assert affected == 1
    args = cursor.execute.call_args.args[1]
    assert args[0] == "ERROR"
    assert args[3] == "connection timeout"


def test_fail_upload_task_defaults_empty_error_message(monkeypatch):
    _, cursor = _mock_db(monkeypatch, rowcount=1)

    task_manager.fail_upload_task(10)

    args = cursor.execute.call_args.args[1]
    assert args[3] == ""
