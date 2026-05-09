import pytest
import csv
import io
from unittest.mock import patch, MagicMock
from datetime import date, datetime
from tickercollector.generator import create_price_report_by_av, get_business_date, tickers

@patch('tickercollector.generator.time.sleep')
@patch.dict('os.environ', {'AV_API_KEY': 'demo'}, clear=True)
@patch('tickercollector.generator.datetime')
@patch('tickercollector.generator.requests.get')
def test_create_price_report_by_av_success(mock_get, mock_datetime, mock_sleep):
    """Verify AV function returns OHLC data rows for all tickers"""
    mock_datetime.now.return_value = datetime(2026, 2, 27, 10, 30)

    def build_response(symbol):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "Time Series (Daily)": {
                "2026-02-27": {
                    "1. open": "201.11",
                    "2. high": "202.22",
                    "3. low": "200.33",
                    "4. close": "201.44",
                    "5. volume": "88331081"
                }
            }
        }
        return response

    mock_get.side_effect = lambda *args, **kwargs: build_response(kwargs['params']['symbol'])

    content, filename = create_price_report_by_av()

    assert filename.startswith("eod_price_av_")
    assert filename.endswith(".csv")

    rows = list(csv.reader(io.StringIO(content)))
    assert rows[0] == ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']
    assert len(rows) == len(tickers) + 1
    assert [row[1] for row in rows[1:]] == tickers

    for row in rows[1:]:
        assert row[0] == '2026-02-27'
        assert row[2:] == ['201.11', '202.22', '200.33', '201.44', '88331081']


@patch.dict('os.environ', {}, clear=True)
@patch('tickercollector.generator.requests.get')
def test_create_price_report_by_av_without_api_key_returns_na(mock_get):
    """Verify AV function returns N/A rows and skips HTTP when API key is missing"""
    content, _ = create_price_report_by_av()

    rows = list(csv.reader(io.StringIO(content)))
    assert rows[0] == ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']
    assert len(rows) == len(tickers) + 1

    for row, symbol in zip(rows[1:], tickers):
        assert row[1] == symbol
        assert row[2:] == ['N/A', 'N/A', 'N/A', 'N/A', 'N/A']

    mock_get.assert_not_called()


@patch('tickercollector.generator.time.sleep')
@patch.dict('os.environ', {'AV_API_KEY': 'demo'}, clear=True)
@patch('tickercollector.generator.datetime')
@patch('tickercollector.generator.requests.get')
def test_create_price_report_by_av_handles_request_failure_per_ticker(mock_get, mock_datetime, mock_sleep):
    """Verify AV function falls back to N/A for failed ticker requests only"""
    mock_datetime.now.return_value = datetime(2026, 2, 27, 10, 30)

    def side_effect(*args, **kwargs):
        symbol = kwargs['params']['symbol']
        if symbol == 'MSFT':
            raise Exception("rate limit")

        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "Time Series (Daily)": {
                "2026-02-27": {
                    "1. open": "10",
                    "2. high": "12",
                    "3. low": "9",
                    "4. close": "11",
                    "5. volume": "99999"
                }
            }
        }
        return response

    mock_get.side_effect = side_effect

    content, _ = create_price_report_by_av()
    rows = list(csv.reader(io.StringIO(content)))

    assert len(rows) == len(tickers) + 1
    row_by_symbol = {row[1]: row for row in rows[1:]}

    assert row_by_symbol['MSFT'][2:] == ['N/A', 'N/A', 'N/A', 'N/A', 'N/A']
    assert row_by_symbol['AAPL'][2:] == ['10.00', '12.00', '9.00', '11.00', '99999']
    assert row_by_symbol['GOOGL'][2:] == ['10.00', '12.00', '9.00', '11.00', '99999']


@patch('tickercollector.generator.time.sleep')
@patch.dict('os.environ', {'AV_API_KEY': 'demo'}, clear=True)
@patch('tickercollector.generator.requests.get')
def test_create_price_report_by_av_handles_missing_time_series_payload(mock_get, mock_sleep):
    """Verify AV function returns N/A rows when response has no Time Series data"""
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "Note": "Thank you for using Alpha Vantage! Our standard API rate limit is 25 requests per day."
    }
    mock_get.return_value = response

    content, _ = create_price_report_by_av()
    rows = list(csv.reader(io.StringIO(content)))

    assert rows[0] == ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']
    assert len(rows) == len(tickers) + 1

    for row, symbol in zip(rows[1:], tickers):
        assert row[1] == symbol
        assert row[2:] == ['N/A', 'N/A', 'N/A', 'N/A', 'N/A']


@patch('tickercollector.generator.time.sleep')
@patch.dict('os.environ', {'AV_API_KEY': 'demo'}, clear=True)
@patch('tickercollector.generator.datetime')
@patch('tickercollector.generator.requests.get')
def test_create_price_report_by_av_handles_malformed_ohlc_values(mock_get, mock_datetime, mock_sleep):
    """Verify AV function falls back to N/A when OHLC values are not numeric"""
    mock_datetime.now.return_value = datetime(2026, 2, 27, 10, 30)

    def side_effect(*args, **kwargs):
        symbol = kwargs['params']['symbol']
        response = MagicMock()
        response.raise_for_status.return_value = None

        if symbol == 'AAPL':
            response.json.return_value = {
                "Time Series (Daily)": {
                    "2026-02-27": {
                        "1. open": "not-a-number",
                        "2. high": "12",
                        "3. low": "9",
                        "4. close": "11",
                        "5. volume": "99999"
                    }
                }
            }
        else:
            response.json.return_value = {
                "Time Series (Daily)": {
                    "2026-02-27": {
                        "1. open": "10",
                        "2. high": "12",
                        "3. low": "9",
                        "4. close": "11",
                        "5. volume": "99999"
                    }
                }
            }
        return response

    mock_get.side_effect = side_effect

    content, _ = create_price_report_by_av()
    rows = list(csv.reader(io.StringIO(content)))
    row_by_symbol = {row[1]: row for row in rows[1:]}

    assert row_by_symbol['AAPL'][2:] == ['N/A', 'N/A', 'N/A', 'N/A', 'N/A']
    assert row_by_symbol['GOOGL'][2:] == ['10.00', '12.00', '9.00', '11.00', '99999']


@patch('tickercollector.generator.time.sleep')
@patch.dict('os.environ', {'AV_API_KEY': 'demo'}, clear=True)
@patch('tickercollector.generator.datetime')
@patch('tickercollector.generator.requests.get')
def test_create_price_report_by_av_handles_rate_limit(mock_get, mock_datetime, mock_sleep):
    """Verify AV function writes N/A for all tickers when the API returns a rate-limit Information payload"""
    mock_datetime.now.return_value = datetime(2026, 2, 27, 10, 30)

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "Information": "Thank you for using Alpha Vantage! Our standard API rate limit is 25 requests per day."
    }
    mock_get.return_value = response

    content, _ = create_price_report_by_av()
    rows = list(csv.reader(io.StringIO(content)))

    assert len(rows) == len(tickers) + 1
    for row, symbol in zip(rows[1:], tickers):
        assert row[1] == symbol
        assert row[2:] == ['N/A', 'N/A', 'N/A', 'N/A', 'N/A']


def test_get_business_date_returns_friday_for_saturday():
    """A Saturday should roll back to the preceding Friday"""
    with patch('tickercollector.generator.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 5, 9, 10, 0)  # Saturday
        result = get_business_date()
    assert result == date(2026, 5, 8)  # Friday


def test_get_business_date_returns_friday_for_sunday():
    """A Sunday should roll back to the preceding Friday"""
    with patch('tickercollector.generator.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 5, 10, 10, 0)  # Sunday
        result = get_business_date()
    assert result == date(2026, 5, 8)  # Friday


def test_get_business_date_skips_us_federal_holiday():
    """New Year's Day (2026-01-01, Thursday) should roll back to 2025-12-31"""
    with patch('tickercollector.generator.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 1, 1, 10, 0)
        result = get_business_date()
    assert result == date(2025, 12, 31)


def test_get_business_date_skips_holiday_on_monday():
    """Memorial Day 2026 (2026-05-25, Monday) should roll back to Friday 2026-05-22"""
    with patch('tickercollector.generator.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 5, 25, 10, 0)
        result = get_business_date()
    assert result == date(2026, 5, 22)