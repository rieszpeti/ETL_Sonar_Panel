import json
import os

from dotenv import load_dotenv
from src.extract_historical_stock_data import download_stock_data
from src.extract_news import fetch_news_articles


def load_config(config_file):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config


if __name__ == "__main__":
    # Load configuration from JSON file
    config = load_config('config.json')

    # Extract parameters from config
    stock_symbols = config['symbols']
    start_date = config['start']
    end_date = config['end']
    db_name = config['db']

    api_key = os.getenv('NEWS_API_KEY')
    if not api_key:
        print("API key is missing. Please check your .env file.")

    # Download stock data
    stock_data = download_stock_data(stock_symbols, start_date, end_date)

    query = 'stock market'
    articles = fetch_news_articles(api_key, query)

    # Save data to database if data was downloaded
    if stock_data is not None:
        save_to_database(stock_data, stock_symbols, db_name)
