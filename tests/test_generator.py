import pytest
import csv
import io
from unittest.mock import patch, MagicMock
from datetime import datetime
from dailyticker.generator import create_price_report  # create_price_report_by_yf

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


# @patch('dailyticker.generator.yf.download')
# def test_create_price_report_by_yf_format(mock_download):
#     """Verify that create_price_report_by_yf produces valid CSV with correct headers"""
#     # Mock yfinance data
#     mock_data = pd.DataFrame({
#         ('Open', 'AAPL'): [150.0],
#         ('High', 'AAPL'): [155.0],
#         ('Low', 'AAPL'): [149.0],
#         ('Close', 'AAPL'): [154.0],
#         ('Open', 'GOOGL'): [2800.0],
#         ('High', 'GOOGL'): [2850.0],
#         ('Low', 'GOOGL'): [2790.0],
#         ('Close', 'GOOGL'): [2840.0],
#         ('Open', 'MSFT'): [300.0],
#         ('High', 'MSFT'): [305.0],
#         ('Low', 'MSFT'): [298.0],
#         ('Close', 'MSFT'): [303.0],
#         ('Open', 'AMZN'): [3200.0],
#         ('High', 'AMZN'): [3250.0],
#         ('Low', 'AMZN'): [3190.0],
#         ('Close', 'AMZN'): [3240.0],
#         ('Open', 'TSLA'): [800.0],
#         ('High', 'TSLA'): [820.0],
#         ('Low', 'TSLA'): [795.0],
#         ('Close', 'TSLA'): [815.0],
#         ('Open', 'TD.TO'): [75.0],
#         ('High', 'TD.TO'): [77.0],
#         ('Low', 'TD.TO'): [74.0],
#         ('Close', 'TD.TO'): [76.0],
#         ('Open', 'SHOP.TO'): [85.0],
#         ('High', 'SHOP.TO'): [88.0],
#         ('Low', 'SHOP.TO'): [84.0],
#         ('Close', 'SHOP.TO'): [87.0],
#     }, index=pd.DatetimeIndex(['2024-01-15']))
#     mock_data.columns = pd.MultiIndex.from_tuples(mock_data.columns)
#     mock_download.return_value = mock_data
#     
#     # Call the function
#     content, filename = create_price_report_by_yf()
#     
#     # Check filename pattern
#     assert filename.startswith("stock_price_")
#     assert filename.endswith(".csv")
#     
#     # Check content structure
#     file_handle = io.StringIO(content)
#     reader = csv.reader(file_handle)
#     rows = list(reader)
#     
#     # Assert header is correct
#     assert rows[0] == ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close']
#     # Assert we have data rows (7 tickers)
#     assert len(rows) == 8  # 1 header + 7 data rows


# @patch('dailyticker.generator.yf.download')
# def test_create_price_report_by_yf_data_content(mock_download):
#     """Verify that create_price_report_by_yf contains correct OHLC data"""
#     # Mock yfinance data
#     test_date = '2024-01-15'
#     mock_data = pd.DataFrame({
#         ('Open', 'AAPL'): [150.0],
#         ('High', 'AAPL'): [155.0],
#         ('Low', 'AAPL'): [149.0],
#         ('Close', 'AAPL'): [154.0],
#         ('Open', 'GOOGL'): [2800.0],
#         ('High', 'GOOGL'): [2850.0],
#         ('Low', 'GOOGL'): [2790.0],
#         ('Close', 'GOOGL'): [2840.0],
#         ('Open', 'MSFT'): [300.0],
#         ('High', 'MSFT'): [305.0],
#         ('Low', 'MSFT'): [298.0],
#         ('Close', 'MSFT'): [303.0],
#         ('Open', 'AMZN'): [3200.0],
#         ('High', 'AMZN'): [3250.0],
#         ('Low', 'AMZN'): [3190.0],
#         ('Close', 'AMZN'): [3240.0],
#         ('Open', 'TSLA'): [800.0],
#         ('High', 'TSLA'): [820.0],
#         ('Low', 'TSLA'): [795.0],
#         ('Close', 'TSLA'): [815.0],
#         ('Open', 'TD.TO'): [75.0],
#         ('High', 'TD.TO'): [77.0],
#         ('Low', 'TD.TO'): [74.0],
#         ('Close', 'TD.TO'): [76.0],
#         ('Open', 'SHOP.TO'): [85.0],
#         ('High', 'SHOP.TO'): [88.0],
#         ('Low', 'SHOP.TO'): [84.0],
#         ('Close', 'SHOP.TO'): [87.0],
#     }, index=pd.DatetimeIndex([test_date]))
#     mock_data.columns = pd.MultiIndex.from_tuples(mock_data.columns)
#     mock_download.return_value = mock_data
#     
#     # Call the function
#     content, filename = create_price_report_by_yf()
#     
#     # Parse CSV content
#     file_handle = io.StringIO(content)
#     reader = csv.reader(file_handle)
#     rows = list(reader)
#     
#     # Check AAPL data
#     aapl_row = rows[1]
#     assert aapl_row[0] == test_date
#     assert aapl_row[1] == 'AAPL'
#     assert aapl_row[2] == '150.00'
#     assert aapl_row[3] == '155.00'
#     assert aapl_row[4] == '149.00'
#     assert aapl_row[5] == '154.00'


# @patch('dailyticker.generator.yf.download')
# def test_create_price_report_by_yf_all_tickers(mock_download):
#     """Verify that all expected tickers are in the report"""
#     # Mock yfinance data
#     mock_data = pd.DataFrame({
#         ('Open', 'AAPL'): [150.0],
#         ('High', 'AAPL'): [155.0],
#         ('Low', 'AAPL'): [149.0],
#         ('Close', 'AAPL'): [154.0],
#         ('Open', 'GOOGL'): [2800.0],
#         ('High', 'GOOGL'): [2850.0],
#         ('Low', 'GOOGL'): [2790.0],
#         ('Close', 'GOOGL'): [2840.0],
#         ('Open', 'MSFT'): [300.0],
#         ('High', 'MSFT'): [305.0],
#         ('Low', 'MSFT'): [298.0],
#         ('Close', 'MSFT'): [303.0],
#         ('Open', 'AMZN'): [3200.0],
#         ('High', 'AMZN'): [3250.0],
#         ('Low', 'AMZN'): [3190.0],
#         ('Close', 'AMZN'): [3240.0],
#         ('Open', 'TSLA'): [800.0],
#         ('High', 'TSLA'): [820.0],
#         ('Low', 'TSLA'): [795.0],
#         ('Close', 'TSLA'): [815.0],
#         ('Open', 'TD.TO'): [75.0],
#         ('High', 'TD.TO'): [77.0],
#         ('Low', 'TD.TO'): [74.0],
#         ('Close', 'TD.TO'): [76.0],
#         ('Open', 'SHOP.TO'): [85.0],
#         ('High', 'SHOP.TO'): [88.0],
#         ('Low', 'SHOP.TO'): [84.0],
#         ('Close', 'SHOP.TO'): [87.0],
#     }, index=pd.DatetimeIndex(['2024-01-15']))
#     mock_data.columns = pd.MultiIndex.from_tuples(mock_data.columns)
#     mock_download.return_value = mock_data
#     
#     # Call the function
#     content, filename = create_price_report_by_yf()
#     
#     # Parse CSV content
#     file_handle = io.StringIO(content)
#     reader = csv.reader(file_handle)
#     rows = list(reader)
#     
#     # Extract tickers from data rows
#     tickers = [row[1] for row in rows[1:]]
#     
#     # Assert all expected tickers are present
#     expected_tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'TD.TO', 'SHOP.TO']
#     assert tickers == expected_tickers


# @patch('dailyticker.generator.yf.download')
# def test_create_price_report_by_yf_handles_exceptions(mock_download):
#     """Verify that the function handles missing data gracefully"""
#     # Mock yfinance data with incomplete data that will raise exceptions
#     mock_data = pd.DataFrame({
#         ('Open', 'AAPL'): [150.0],
#         ('High', 'AAPL'): [155.0],
#         ('Low', 'AAPL'): [149.0],
#         ('Close', 'AAPL'): [154.0],
#     }, index=pd.DatetimeIndex(['2024-01-15']))
#     mock_data.columns = pd.MultiIndex.from_tuples(mock_data.columns)
#     
#     # Make xs method raise an exception for some tickers
#     def xs_side_effect(*args, **kwargs):
#         ticker = args[0]
#         if ticker in ['GOOGL', 'MSFT', 'TD.TO']:
#             raise KeyError(f"Ticker {ticker} not found")
#         return mock_data.xs(ticker, axis=1, level=1)
#     
#     mock_data.xs = MagicMock(side_effect=xs_side_effect)
#     mock_download.return_value = mock_data
#     
#     # Call the function - should not raise an exception
#     content, filename = create_price_report_by_yf()
#     
#     # Parse CSV content
#     file_handle = io.StringIO(content)
#     reader = csv.reader(file_handle)
#     rows = list(reader)
#     
#     # Should still have all 7 tickers with N/A for failed ones
#     assert len(rows) == 8  # 1 header + 7 data rows
#     
#     # Check that some rows have N/A values
#     has_na = any('N/A' in row for row in rows[1:])
#     assert has_na


# @patch('dailyticker.generator.yf.download')
# def test_create_price_report_by_yf_date_format(mock_download):
#     """Verify that the business date is formatted correctly"""
#     # Mock yfinance data
#     test_date = datetime(2024, 1, 15)
#     mock_data = pd.DataFrame({
#         ('Open', 'AAPL'): [150.0],
#         ('High', 'AAPL'): [155.0],
#         ('Low', 'AAPL'): [149.0],
#         ('Close', 'AAPL'): [154.0],
#         ('Open', 'GOOGL'): [2800.0],
#         ('High', 'GOOGL'): [2850.0],
#         ('Low', 'GOOGL'): [2790.0],
#         ('Close', 'GOOGL'): [2840.0],
#         ('Open', 'MSFT'): [300.0],
#         ('High', 'MSFT'): [305.0],
#         ('Low', 'MSFT'): [298.0],
#         ('Close', 'MSFT'): [303.0],
#         ('Open', 'AMZN'): [3200.0],
#         ('High', 'AMZN'): [3250.0],
#         ('Low', 'AMZN'): [3190.0],
#         ('Close', 'AMZN'): [3240.0],
#         ('Open', 'TSLA'): [800.0],
#         ('High', 'TSLA'): [820.0],
#         ('Low', 'TSLA'): [795.0],
#         ('Close', 'TSLA'): [815.0],
#         ('Open', 'TD.TO'): [75.0],
#         ('High', 'TD.TO'): [77.0],
#         ('Low', 'TD.TO'): [74.0],
#         ('Close', 'TD.TO'): [76.0],
#         ('Open', 'SHOP.TO'): [85.0],
#         ('High', 'SHOP.TO'): [88.0],
#         ('Low', 'SHOP.TO'): [84.0],
#         ('Close', 'SHOP.TO'): [87.0],
#     }, index=pd.DatetimeIndex([test_date]))
#     mock_data.columns = pd.MultiIndex.from_tuples(mock_data.columns)
#     mock_download.return_value = mock_data
#     
#     # Call the function
#     content, filename = create_price_report_by_yf()
#     
#     # Parse CSV content
#     file_handle = io.StringIO(content)
#     reader = csv.reader(file_handle)
#     rows = list(reader)
#     
#     # Check date format in all data rows
#     for row in rows[1:]:
#         assert row[0] == '2024-01-15'  # YYYY-MM-DD format


# @patch('dailyticker.generator.yf.download')
# def test_create_price_report_by_yf_price_formatting(mock_download):
#     """Verify that prices are formatted to 2 decimal places"""
#     # Mock yfinance data with prices that have more decimals
#     mock_data = pd.DataFrame({
#         ('Open', 'AAPL'): [150.123456],
#         ('High', 'AAPL'): [155.987654],
#         ('Low', 'AAPL'): [149.111111],
#         ('Close', 'AAPL'): [154.555555],
#         ('Open', 'GOOGL'): [2800.0],
#         ('High', 'GOOGL'): [2850.0],
#         ('Low', 'GOOGL'): [2790.0],
#         ('Close', 'GOOGL'): [2840.0],
#         ('Open', 'MSFT'): [300.0],
#         ('High', 'MSFT'): [305.0],
#         ('Low', 'MSFT'): [298.0],
#         ('Close', 'MSFT'): [303.0],
#         ('Open', 'AMZN'): [3200.0],
#         ('High', 'AMZN'): [3250.0],
#         ('Low', 'AMZN'): [3190.0],
#         ('Close', 'AMZN'): [3240.0],
#         ('Open', 'TSLA'): [800.0],
#         ('High', 'TSLA'): [820.0],
#         ('Low', 'TSLA'): [795.0],
#         ('Close', 'TSLA'): [815.0],
#         ('Open', 'TD.TO'): [75.123456],
#         ('High', 'TD.TO'): [76.987654],
#         ('Low', 'TD.TO'): [74.111111],
#         ('Close', 'TD.TO'): [75.555555],
#         ('Open', 'SHOP.TO'): [85.123456],
#         ('High', 'SHOP.TO'): [87.987654],
#         ('Low', 'SHOP.TO'): [84.111111],
#         ('Close', 'SHOP.TO'): [86.555555],
#     }, index=pd.DatetimeIndex(['2024-01-15']))
#     mock_data.columns = pd.MultiIndex.from_tuples(mock_data.columns)
#     mock_download.return_value = mock_data
#     
#     # Call the function
#     content, filename = create_price_report_by_yf()
#     
#     # Parse CSV content
#     file_handle = io.StringIO(content)
#     reader = csv.reader(file_handle)
#     rows = list(reader)
#     
#     # Check AAPL prices are formatted to 2 decimal places
#     aapl_row = rows[1]
#     assert aapl_row[2] == '150.12'
#     assert aapl_row[3] == '155.99'
#     assert aapl_row[4] == '149.11'
#     assert aapl_row[5] == '154.56'