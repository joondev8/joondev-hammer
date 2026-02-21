#import yfinance as yf
import csv
import io
from datetime import datetime


def create_price_report():
    """
    Generates report data and returns a tuple of (content, filename)
    """
    # Create a unique filename
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    filename = f"stock_price_{timestamp}.csv"
    
    # 3. Extract the actual Business Date from the DataFrame index
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

# def create_price_report_by_yf():
#     """
#     Generates OHLC report data including the specific business date.
#     """
#     # 1. Create a unique filename for the output file
#     timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
#     filename = f"stock_price_{timestamp}.csv"
#     
#     tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'TD.TO', 'SHOP.TO']
# 
#     # 2. Download the last 1 day of data
#     data = yf.download(tickers, period="1d", auto_adjust=True)
# 
#     # 3. Extract the actual Business Date from the DataFrame index
#     # data.index[-1] gives the timestamp of the last row
#     business_date = data.index[-1].strftime('%Y-%m-%d')
#     
# 
#     # 4. Generate data in memory
#     output = io.StringIO()
#     writer = csv.writer(output)
#     
#     # Updated Header with 'Date'
#     writer.writerow(['Date', 'Ticker', 'Open', 'High', 'Low', 'Close'])
#     
#     # 5. Iterate and extract OHLC data
#     for ticker in tickers:
#         try:
#             # Handle MultiIndex for multiple tickers
#             ohlc = data.xs(ticker, axis=1, level=1) if len(tickers) > 1 else data
#             
#             # Create the row with the business date included
#             row = [
#                 business_date,
#                 ticker,
#                 f"{ohlc['Open'].iloc[-1]:.2f}",
#                 f"{ohlc['High'].iloc[-1]:.2f}",
#                 f"{ohlc['Low'].iloc[-1]:.2f}",
#                 f"{ohlc['Close'].iloc[-1]:.2f}"
#             ]
#             writer.writerow(row)
#         except Exception:
#             writer.writerow([business_date, ticker, "N/A", "N/A", "N/A", "N/A"])
#     
#     return output.getvalue(), filename

def main():
    content, filename = create_price_report()
    print(f"Generated report: {filename}")
    print(content)

if __name__ == "__main__":
    main()
