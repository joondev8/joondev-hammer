import pytest
import csv
import io
from dailyticker.generator import create_price_report

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
    assert rows[0] == ['ID', 'Transaction_Date', 'Amount', 'Currency']
    # Assert we have data rows
    assert len(rows) > 1