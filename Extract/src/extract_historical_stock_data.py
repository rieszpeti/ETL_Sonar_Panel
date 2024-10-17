import yfinance as yf

def download_stock_data(symbols, start, end):
    """Download historical stock data for the given symbols."""
    try:
        # Download historical data for multiple stocks
        data = yf.download(symbols, start=start, end=end)
        print("Data downloaded successfully.")
        return data
    except Exception as e:
        print(f"Error downloading data: {e}")
        return None
