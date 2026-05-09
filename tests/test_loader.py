from unittest.mock import MagicMock

import pytest

from tickerloader import loader


def _mock_db(monkeypatch):
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.__exit__.return_value = None

    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.__exit__.return_value = None

    connection.cursor.return_value = cursor
    monkeypatch.setattr(loader, "get_connection", lambda: connection)
    return connection, cursor


# --- insert_rows ---

def test_insert_rows_returns_zero_for_empty_input(monkeypatch):
    _mock_db(monkeypatch)
    inserted = loader.insert_rows([], 1)

    assert inserted == 0


def test_insert_rows_inserts_only_valid_rows(monkeypatch):
    _, cursor = _mock_db(monkeypatch)

    rows = [
        {
            "business_date": "2026-02-28",
            "ticker": "AAPL",
            "open_price": "100.1",
            "high_price": "110.2",
            "low_price": "99.9",
            "close_price": "105.5",
        },
        {
            "Date": "2026-02-28",
            "Ticker": "MSFT",
            "Open": "200",
            "High": "210",
            "Low": "190",
            "Close": "205",
        },
        {
            "business_date": "2026-02-28",
            "ticker": "GOOGL",
            "open_price": "50",
            "high_price": "55",
            "low_price": "49",
            # missing close_price — should be skipped
        },
    ]

    inserted = loader.insert_rows(rows, 42)

    assert inserted == 2
    cursor.executemany.assert_called_once()
    _, inserted_rows = cursor.executemany.call_args.args
    assert inserted_rows == [
        ("2026-02-28", "AAPL", 100.1, 110.2, 99.9, 105.5, 42),
        ("2026-02-28", "MSFT", 200.0, 210.0, 190.0, 205.0, 42),
    ]


def test_insert_rows_skips_na_numeric_values(monkeypatch):
    _, cursor = _mock_db(monkeypatch)

    rows = [
        {
            "business_date": "2026-02-28",
            "ticker": "AAPL",
            "open_price": "NA",
            "high_price": "110.2",
            "low_price": "99.9",
            "close_price": "105.5",
        },
    ]

    inserted = loader.insert_rows(rows, 1)

    assert inserted == 0
    cursor.executemany.assert_not_called()


def test_insert_rows_skips_invalid_numeric_values(monkeypatch):
    _, cursor = _mock_db(monkeypatch)

    rows = [
        {
            "business_date": "2026-02-28",
            "ticker": "AAPL",
            "open_price": "not-a-number",
            "high_price": "110.2",
            "low_price": "99.9",
            "close_price": "105.5",
        },
    ]

    inserted = loader.insert_rows(rows, 1)

    assert inserted == 0
    cursor.executemany.assert_not_called()


# --- parse_rows ---

def test_parse_rows_returns_correct_shape():
    csv_content = "Date,Ticker,Open,High,Low,Close\n2026-03-09,AAPL,100,110,99,105\n"
    rows = loader.parse_rows(csv_content)

    assert len(rows) == 1
    assert rows[0] == {
        "business_date": "2026-03-09",
        "ticker": "AAPL",
        "open_price": "100",
        "high_price": "110",
        "low_price": "99",
        "close_price": "105",
    }


# --- load_report_to_db ---

def test_load_report_to_db_success(monkeypatch):
    csv_content = "Date,Ticker,Open,High,Low,Close\n2026-03-09,AAPL,100,110,99,105\n"
    monkeypatch.setattr(loader, "download_csv_from_s3", lambda bucket, key: csv_content)
    monkeypatch.setattr(loader, "new_upload_task", lambda *args: 1)
    monkeypatch.setattr(loader, "complete_upload_task", MagicMock())
    monkeypatch.setattr(loader, "insert_rows", lambda rows, task_id: len(rows))

    result = loader.load_report_to_db("test-bucket", "eod_price_av_20260309_20260309_2200.csv")

    assert result["status"] == "success"
    assert result["source_bucket"] == "test-bucket"
    assert result["source_key"] == "eod_price_av_20260309_20260309_2200.csv"
    assert result["rows_parsed"] == 1
    assert result["rows_inserted"] == 1


def test_load_report_to_db_marks_task_failed_on_error(monkeypatch):
    def _raise(*args):
        raise RuntimeError("S3 error")

    monkeypatch.setattr(loader, "new_upload_task", lambda *args: 99)
    monkeypatch.setattr(loader, "download_csv_from_s3", _raise)
    fail_mock = MagicMock()
    monkeypatch.setattr(loader, "fail_upload_task", fail_mock)

    with pytest.raises(RuntimeError, match="S3 error"):
        loader.load_report_to_db("test-bucket", "eod_price_av_20260309_20260309_2200.csv")

    fail_mock.assert_called_once_with(99, "S3 error")
