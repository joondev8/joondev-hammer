from unittest.mock import MagicMock

from tickerloader import loader


def _mock_db(monkeypatch, rowcount: int = 0, fetchone_value=None):
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.__exit__.return_value = None

    cursor = MagicMock()
    cursor.rowcount = rowcount
    cursor.fetchone.return_value = fetchone_value
    cursor.__enter__.return_value = cursor
    cursor.__exit__.return_value = None

    connection.cursor.return_value = cursor
    monkeypatch.setattr(loader, "_connect_to_db", lambda: connection)
    return connection, cursor


def test_insert_rows_returns_zero_for_empty_input(monkeypatch):
    _mock_db(monkeypatch)
    inserted = loader.insert_rows([], 1)

    assert inserted == 0


def test_insert_rows_inserts_only_valid_rows(monkeypatch):
    _, cursor = _mock_db(monkeypatch, rowcount=2)

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


def test_insert_upload_task_and_update_status(monkeypatch):
    _, cursor = _mock_db(monkeypatch, rowcount=1, fetchone_value=(123,))

    task_id = loader.insert_upload_task(
        business_date="2026-02-28",
        source_bucket="test-bucket",
        source_key="2026-02-28.csv",
        data_source="av",
        status="IN_PROGRESS",
    )

    assert task_id > 0
    cursor.execute.assert_called_once()

    updated_rows = loader.update_upload_task_status(task_id, 10, 2, "DONE")

    assert updated_rows == 1


def test_update_upload_task_status_returns_zero_for_missing_task(monkeypatch):
    _, cursor = _mock_db(monkeypatch, rowcount=0)

    updated_rows = loader.update_upload_task_status(9999, 0, 0, "ERROR")

    assert updated_rows == 0
    cursor.execute.assert_called_once()
