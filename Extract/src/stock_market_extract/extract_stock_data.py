import json
import logging
import pandas as pd
import yfinance as yf
import psycopg2
from psycopg2 import sql
from psycopg2 import IntegrityError

class DatabaseUnavailableException(Exception):
    """Custom exception for database unavailability."""
    pass

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

def is_database_available(db_url):
    """Check if the database is available."""
    logging.info(f"Database URL: {db_url}")
    try:
        connection = psycopg2.connect(db_url)
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        connection.close()
        return True
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return False

def save_high_to_database(data, db_url):
    """Save only the close price of the downloaded stock data to the database, avoiding duplicates."""

    if not is_database_available(db_url):
        logging.error("Database is not available. Aborting save operation.")
        raise DatabaseUnavailableException("Database is not available.")

    tickers = data.columns[1:]
    last_date = None

    try:
        connection = psycopg2.connect(db_url)
        with connection:
            with connection.cursor() as cursor:
                for date_value, row in data.iterrows():
                    for ticker in tickers:
                        try:
                            if str(ticker[0]) == "High":
                                price = row[ticker]
                                if pd.notna(price):
                                    sql_str = sql.SQL("""
                                        INSERT INTO stock.stock_data (symbol, date, price)
                                        VALUES (%s, %s, %s)
                                        ON CONFLICT (symbol, date) DO NOTHING;
                                    """)
                                    cursor.execute(sql_str, (str(ticker[1]), date_value, float(price)))
                                    logging.info(f"Saved high price for {ticker} on {date_value}: {price}")
                                    last_date = date_value
                        except IntegrityError:
                            # Ignore duplicates
                            logging.warning(f"Duplicate entry for {ticker} on {date_value} skipped.")
                        except Exception as e:
                            # Access the variable date_value carefully in the error logging
                            logging.error(f"Error saving data for {ticker} on {date_value}: {e}")

    finally:
        if connection:
            connection.close()

    if last_date is not None:
        update_stock_market_config(last_date)

def update_stock_market_config(last_date):
    """Update the stock market config JSON file with the last processed date."""
    config_path = 'stock_market_config.json'
    config_data = {
        "stock_market": {
            "symbols": ["FSLR", "ENPH", "SEDG", "CSIQ", "RUN", "ARRY"],
            "query_start": last_date.isoformat()
        }
    }

    with open(config_path, 'w') as json_file:
        json.dump(config_data, json_file, indent=4)
    logging.info(f"Updated stock_market_config.json with last date: {last_date}")
