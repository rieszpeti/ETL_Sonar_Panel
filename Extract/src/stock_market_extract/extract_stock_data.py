import json
import logging
import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


def download_stock_data(symbols, start, end):
    """Download historical stock data for the given symbols."""
    try:
        # Download historical data for multiple stocks
        data = yf.download(symbols, start=start, end=end)
        logging.info("Data downloaded successfully.")
        return data
    except Exception as e:
        logging.error(f"Error downloading data: {e}")
        return None


def save_high_to_database(data, db_url):
    """Save only the close price of the downloaded stock data to the database, avoiding duplicates."""
    engine = create_engine(db_url)

    tickers = data.columns[1:]

    with engine.connect() as conn:
        for date_value, row in data.iterrows():
            for ticker in tickers:
                try:
                    price = row[ticker]
                    if pd.notna(price):
                        sql_str = text(f"""
                            INSERT INTO stock.stock_data (symbol, date, price)
                            VALUES (:symbol, :date, :price)
                            ON CONFLICT (symbol, date) DO NOTHING;
                        """)
                        conn.execute(sql_str, {"symbol": str(ticker[1]), "date": date_value, "price": float(price)})
                        logging.info(f"Saved high price for {ticker} on {date_value}: {price}")
                except IntegrityError:
                    # Ignore duplicates
                    logging.warning(f"Duplicate entry for {ticker} on {date_value} skipped.")
                except Exception as e:
                    # Access the variable date_value carefully in the error logging
                    logging.error(f"Error saving data for {ticker} on {date_value}: {e}")
