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
    
    # Generate data in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header and dummy data
    writer.writerow(['ID', 'Transaction_Date', 'Amount', 'Currency'])
    writer.writerow(['101', datetime.now().isoformat(), '250.00', 'USD'])
    writer.writerow(['102', datetime.now().isoformat(), '15.50', 'CAD'])
    
    return output.getvalue(), filename