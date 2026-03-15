import csv
import io
import os
import requests
import logging
from datetime import datetime

tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'TD.TO', 'SHOP.TO']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_price_report():
    """
    Generates report data and returns a tuple of (content, filename)
    """
    # Create a unique filename for the output file
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    filename = f"stock_price_{timestamp}.csv"
    
    # Extract the actual Business Date from the DataFrame index
    # data.index[-1] gives the timestamp of the last row
    business_date = datetime.now().strftime('%Y-%m-%d')

    # Generate data in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Updated Header with 'Date'
    writer.writerow(['Date', 'Ticker', 'Open', 'High', 'Low', 'Close'])    
    writer.writerow([business_date, 'AAPL', '250.00', '250.00', '250.00', '250.00'])
    writer.writerow([business_date, 'GOOGL', '15.50', '15.50', '15.50', '15.50'])
    writer.writerow([business_date, 'MSFT', '100.50', '100.50', '100.50', '100.50'])
    
    return output.getvalue(), filename

def create_price_report_by_av():
    """
    Generates OHLC report data including the specific business date.
    Use Alpha Vantage API to fetch stock data and generate the report.
    """
    api_key = os.getenv("AV_API_KEY")
    base_url = "https://www.alphavantage.co/query"

    # Create a unique filename for the output file
    # The filename includes the current timestamp to ensure uniqueness and traceability. 
    # It has the format "stock_price_{source}_YYYY-MM-DD_HHMM.csv", where {source} is the data source e,g, "av" for Alpha Vantage, while YYYY-MM-DD is the current date, and HHMM is the current time in hours and minutes.
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    filename = f"stock_price_av_{timestamp}.csv"

    # Generate data in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Updated Header with 'Date'
    writer.writerow(['Date', 'Ticker', 'Open', 'High', 'Low', 'Close'])

    for ticker in tickers:
        if not api_key:
            business_date = datetime.now().strftime('%Y-%m-%d')
            writer.writerow([business_date, ticker, "N/A", "N/A", "N/A", "N/A"])
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
            logger.info(f"Response payload for {ticker}: {payload}")

            time_series = payload.get("Time Series (Daily)", {})
            if not time_series:
                business_date = datetime.now().strftime('%Y-%m-%d')
                writer.writerow([business_date, ticker, "N/A", "N/A", "N/A", "N/A"])
                continue

            business_date = max(time_series.keys())
            day_data = time_series[business_date]

            row = [
                business_date,
                ticker,
                f"{float(day_data['1. open']):.2f}",
                f"{float(day_data['2. high']):.2f}",
                f"{float(day_data['3. low']):.2f}",
                f"{float(day_data['4. close']):.2f}",
            ]
            logger.info(f"Writing data for {ticker} on {business_date}: {row}")
            writer.writerow(row)
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            business_date = datetime.now().strftime('%Y-%m-%d')
            writer.writerow([business_date, ticker, "N/A", "N/A", "N/A", "N/A"])
    
    return output.getvalue(), filename

def main():
    content, filename = create_price_report_by_av()
    print(f"Generated report: {filename}")
    print(content)

if __name__ == "__main__":
    main()
