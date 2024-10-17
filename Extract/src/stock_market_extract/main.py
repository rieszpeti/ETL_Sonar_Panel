import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from dotenv import load_dotenv

from logging_config import setup_logging
from extract_stock_data import download_stock_data, save_high_to_database


@dataclass
class StockMarketConfig:
    symbols: List[str] = field(metadata={'required': True})
    query_start: str = field(metadata={'required': True})
    query_end: str = field(default_factory=lambda: datetime.today().strftime('%Y-%m-%d'))

    @classmethod
    def from_json(cls, json_data: str):
        data = json.loads(json_data)
        stock_market_data = data.get('stock_market', {})
        return cls(
            symbols=stock_market_data.get('symbols', []),
            query_start=stock_market_data.get('query_start', ''),
        )

    def __post_init__(self):
        if not self.symbols:
            raise ValueError("The symbols list cannot be empty.")

        try:
            datetime.strptime(self.query_start, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Dates must be in the format 'YYYY-MM-DD'.")


def load_config(filename: str) -> StockMarketConfig:
    try:
        with open(filename, 'r') as file:
            json_data = file.read()
        return StockMarketConfig.from_json(json_data)
    except FileNotFoundError:
        logging.error("Configuration file not found. Please ensure 'stock_market_config.json' exists.")
        raise
    except json.JSONDecodeError:
        logging.error("Error decoding JSON. Please check the format of 'stock_market_config.json'.")
        raise


def main():
    load_dotenv()
    setup_logging()

    try:
        config = load_config('stock_market_config.json')
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        return

    stock_data = download_stock_data(config.symbols, config.query_start, config.query_end)

    if stock_data is not None:
        logging.info("Processing downloaded data...")
        save_high_to_database(stock_data, os.getenv('POSTGRES_DATABASE_URL'))  # Save high prices to database
    else:
        logging.error("No stock data to process.")


if __name__ == "__main__":
    main()
