import pytest
import csv
import io
from unittest.mock import patch, MagicMock
from datetime import datetime
from dailyticker.generator import create_price_report, create_price_report_by_av, tickers

def test_create_price_report_format():
    """Verify that the generator produces a valid CSV with correct headers"""
    content, filename = create_price_report()
    
    # Check filename pattern
    assert filename.startswith("stock_price_")
    assert filename.endswith(".csv")
    
    # Check content structure
    file_handle = io.StringIO(content)
    reader = csv.reader(file_handle)
    rows = list(reader)
    
    # Assert header is correct
    assert rows[0] == ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close']
    # Assert we have data rows (3 tickers: AAPL, GOOGL, MSFT)
    assert len(rows) == 4  # 1 header + 3 data rows
    
    # Verify the tickers are present
    tickers = [row[1] for row in rows[1:]]
    assert tickers == ['AAPL', 'GOOGL', 'MSFT']
    
    # Verify data structure (all rows should have 6 columns)
    for row in rows:
        assert len(row) == 6


@patch.dict('os.environ', {'AV_API_KEY': 'demo'}, clear=True)
@patch('dailyticker.generator.requests.get')
def test_create_price_report_by_av_success(mock_get):
    """Verify AV function returns OHLC data rows for all tickers"""
    def build_response(symbol):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "Time Series (Daily)": {
                "2026-02-27": {
                    "1. open": "101.1",
                    "2. high": "102.2",
                    "3. low": "100.3",
                    "4. close": "101.4"
                },
                "2026-02-28": {
                    "1. open": "201.11",
                    "2. high": "202.22",
                    "3. low": "200.33",
                    "4. close": "201.44"
                }
            }
        }
        return response

    mock_get.side_effect = lambda *args, **kwargs: build_response(kwargs['params']['symbol'])

    content, filename = create_price_report_by_av()

    assert filename.startswith("stock_price_")
    assert filename.endswith(".csv")

    rows = list(csv.reader(io.StringIO(content)))
    assert rows[0] == ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close']
    assert len(rows) == len(tickers) + 1
    assert [row[1] for row in rows[1:]] == tickers

    for row in rows[1:]:
        assert row[0] == '2026-02-28'
        assert row[2:] == ['201.11', '202.22', '200.33', '201.44']


@patch.dict('os.environ', {}, clear=True)
@patch('dailyticker.generator.requests.get')
def test_create_price_report_by_av_without_api_key_returns_na(mock_get):
    """Verify AV function returns N/A rows and skips HTTP when API key is missing"""
    content, _ = create_price_report_by_av()

    rows = list(csv.reader(io.StringIO(content)))
    assert rows[0] == ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close']
    assert len(rows) == len(tickers) + 1

    for row, symbol in zip(rows[1:], tickers):
        assert row[1] == symbol
        assert row[2:] == ['N/A', 'N/A', 'N/A', 'N/A']

    mock_get.assert_not_called()


@patch.dict('os.environ', {'AV_API_KEY': 'demo'}, clear=True)
@patch('dailyticker.generator.requests.get')
def test_create_price_report_by_av_handles_request_failure_per_ticker(mock_get):
    """Verify AV function falls back to N/A for failed ticker requests only"""
    def side_effect(*args, **kwargs):
        symbol = kwargs['params']['symbol']
        if symbol == 'MSFT':
            raise Exception("rate limit")

        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "Time Series (Daily)": {
                "2026-02-28": {
                    "1. open": "10",
                    "2. high": "12",
                    "3. low": "9",
                    "4. close": "11"
                }
            }
        }
        return response

    mock_get.side_effect = side_effect

    content, _ = create_price_report_by_av()
    rows = list(csv.reader(io.StringIO(content)))

    assert len(rows) == len(tickers) + 1
    row_by_symbol = {row[1]: row for row in rows[1:]}

    assert row_by_symbol['MSFT'][2:] == ['N/A', 'N/A', 'N/A', 'N/A']
    assert row_by_symbol['AAPL'][2:] == ['10.00', '12.00', '9.00', '11.00']
    assert row_by_symbol['GOOGL'][2:] == ['10.00', '12.00', '9.00', '11.00']


@patch.dict('os.environ', {'AV_API_KEY': 'demo'}, clear=True)
@patch('dailyticker.generator.requests.get')
def test_create_price_report_by_av_handles_missing_time_series_payload(mock_get):
    """Verify AV function returns N/A rows when response has no Time Series data"""
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "Note": "Thank you for using Alpha Vantage! Our standard API rate limit is 25 requests per day."
    }
    mock_get.return_value = response

    content, _ = create_price_report_by_av()
    rows = list(csv.reader(io.StringIO(content)))

    assert rows[0] == ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close']
    assert len(rows) == len(tickers) + 1

    for row, symbol in zip(rows[1:], tickers):
        assert row[1] == symbol
        assert row[2:] == ['N/A', 'N/A', 'N/A', 'N/A']


@patch.dict('os.environ', {'AV_API_KEY': 'demo'}, clear=True)
@patch('dailyticker.generator.requests.get')
def test_create_price_report_by_av_handles_malformed_ohlc_values(mock_get):
    """Verify AV function falls back to N/A when OHLC values are not numeric"""
    def side_effect(*args, **kwargs):
        symbol = kwargs['params']['symbol']
        response = MagicMock()
        response.raise_for_status.return_value = None

        if symbol == 'AAPL':
            response.json.return_value = {
                "Time Series (Daily)": {
                    "2026-02-28": {
                        "1. open": "not-a-number",
                        "2. high": "12",
                        "3. low": "9",
                        "4. close": "11"
                    }
                }
            }
        else:
            response.json.return_value = {
                "Time Series (Daily)": {
                    "2026-02-28": {
                        "1. open": "10",
                        "2. high": "12",
                        "3. low": "9",
                        "4. close": "11"
                    }
                }
            }
        return response

    mock_get.side_effect = side_effect

    content, _ = create_price_report_by_av()
    rows = list(csv.reader(io.StringIO(content)))
    row_by_symbol = {row[1]: row for row in rows[1:]}

    assert row_by_symbol['AAPL'][2:] == ['N/A', 'N/A', 'N/A', 'N/A']
    assert row_by_symbol['GOOGL'][2:] == ['10.00', '12.00', '9.00', '11.00']