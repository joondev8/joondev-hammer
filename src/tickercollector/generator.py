import csv
import io
import os
import time
import requests
import logging
import holidays
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from tickerloader.db import get_connection

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# def create_price_report():
#     """
#     Generates report data and returns a tuple of (content, filename)
#     """
#     # Create a unique filename for the output file
#     timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
#     filename = f"stock_price_{timestamp}.csv"

#     # Extract the actual Business Date from the DataFrame index
#     # data.index[-1] gives the timestamp of the last row
#     business_date = datetime.now().strftime('%Y-%m-%d')

#     # Generate data in memory
#     output = io.StringIO()
#     writer = csv.writer(output)

#     # Updated Header with 'Date'
#     writer.writerow(['Date', 'Ticker', 'Open', 'High', 'Low', 'Close'])
#     writer.writerow([business_date, 'AAPL', '250.00', '250.00', '250.00', '250.00'])
#     writer.writerow([business_date, 'GOOGL', '15.50', '15.50', '15.50', '15.50'])
#     writer.writerow([business_date, 'MSFT', '100.50', '100.50', '100.50', '100.50'])

#     return output.getvalue(), filename


def create_price_report_by_av():
    """
    Generates OHLC report data including the specific business date.
    Use Alpha Vantage API to fetch stock data and generate the report.
    """
    api_key = os.getenv("AV_API_KEY")
    base_url = "https://www.alphavantage.co/query"

    # Create a unique filename for the output file
    # The filename includes the current timestamp to ensure uniqueness and traceability.    
    business_date = get_business_date().strftime('%Y-%m-%d')
    filename = get_filename("")

    # Generate data in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Updated Header with 'Date'
    writer.writerow(['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume'])

    tickers = get_ticker_list()
    for ticker in tickers:
        if not api_key:
            writer.writerow([business_date, ticker, "N/A", "N/A", "N/A", "N/A", "N/A"])
            continue

        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": "compact",
            "apikey": api_key
        }

        try:
            response = requests.get(base_url, params=params, timeout=15)
            response.raise_for_status()
            payload = response.json()

            logger.info(f"Fetched data for {ticker} from Alpha Vantage")

            if "Information" in payload:
                logger.warning(f"Rate limit hit for {ticker}: {payload['Information']}")
                writer.writerow([business_date, ticker, "N/A", "N/A", "N/A", "N/A", "N/A"])
                continue

            time_series = payload.get("Time Series (Daily)", {})
            day_data = time_series.get(business_date)

            if day_data is None:
                logger.warning(f"No data for {ticker} on {business_date}, writing N/A")
                writer.writerow([business_date, ticker, "N/A", "N/A", "N/A", "N/A", "N/A"])
                continue

            row = [
                business_date,
                ticker,
                f"{float(day_data['1. open']):.2f}",
                f"{float(day_data['2. high']):.2f}",
                f"{float(day_data['3. low']):.2f}",
                f"{float(day_data['4. close']):.2f}",
                day_data['5. volume'],
            ]
            logger.info(f"Writing data for {ticker} on {business_date}: {row}")
            writer.writerow(row)

        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            writer.writerow([business_date, ticker, "N/A", "N/A", "N/A", "N/A", "N/A"])

        finally:
            time.sleep(1.8)

    return output.getvalue(), filename

def get_business_date() -> date:
    """
    Returns the current business date in date format.
    If today is a weekend or holiday in US, it should return the most recent previous business date.
    """
    us_holidays = holidays.US()
    today = datetime.now(ZoneInfo("America/New_York")).date()
    while today.weekday() >= 5 or today in us_holidays:
        today -= timedelta(days=1)
    return today

def get_filename(source: str) -> str:
    """
    Generates a unique filename for the report based on the source and current timestamp.
    The filename format is "eod_price_{source}_{business_date}_MMDD_HHMM.csv".
    {business_date} is the current business date in YYYYMMDD format, and MMDD_HHMM is the current timestamp.
    """
    run_datetime = datetime.now(ZoneInfo("America/New_York"))
    timestamp = run_datetime.strftime('%m%d_%H%M')
    business_date = get_business_date().strftime('%Y%m%d')

    if (not source):
        return f"eod_price_{business_date}_{timestamp}.csv"    
    return f"eod_price_{source}_{business_date}_{timestamp}.csv"

def get_ticker_list() -> list:
    """
    Returns the list of tickers to fetch data for. 
    The list is fetched from database table 'security_master.asset_equity_ticker' where the current business date falls between effective_date and expiry_date.
    Expiry date can be null, which means the ticker is still active.
    Remove duplicates and sort the list alphabetically before returning.
    """
    business_date = get_business_date()
    query = """
        SELECT DISTINCT ticker
        FROM security_master.asset_equity_ticker
        WHERE effective_date <= %s
          AND (expiry_date IS NULL OR expiry_date >= %s)
        ORDER BY ticker
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (business_date, business_date))
            rows = cur.fetchall()

    logger.info(f"Fetched {len(rows)} tickers from database")
    return [row[0] for row in rows]

def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    
    content, filename = create_price_report_by_av()
    print(f"Generated report: {filename}")
    print(content)
    with open(filename, 'w', newline='') as f:
        f.write(content)
    print(f"Saved to {filename}")

if __name__ == "__main__":
    main()
