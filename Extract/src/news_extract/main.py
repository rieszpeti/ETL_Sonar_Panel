import json
import logging
import os
from dataclasses import field, dataclass
from typing import List

from dotenv import load_dotenv

from src.common.logging_config import setup_logging
from src.mongodb_config import MongoDBConfig
from extract_news import fetch_news_articles, perform_sentiment_analysis, upload_to_mongodb


@dataclass
class NewsConfig:
    news_queries: List[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, json_data: str):
        data = json.loads(json_data)
        return cls(
            news_queries=data.get('news_queries', [])
        )


def load_config(filename: str) -> NewsConfig:
    """Load configuration from a JSON file and return NewsConfig."""
    with open(filename, 'r') as file:
        json_data = file.read()
    return NewsConfig.from_json(json_data)


def main():
    load_dotenv()
    setup_logging()

    api_key = os.getenv('NEWS_API_KEY')

    mongo_config = MongoDBConfig(
        connection_string=os.getenv('MONGODB_CONNECTION_STRING'),
        db_name=os.getenv('MONGODB_DB_NAME_NEWS'),
        collection_name=os.getenv('MONGODB_DB_COLLECTION_NEWS')
    )

    if not api_key:
        logging.error("API key is missing. Please check your .env file.")
        return

    try:
        config = load_config('news_config.json')
    except FileNotFoundError:
        logging.error("Configuration file not found. Please ensure 'news_config.json' exists.")
        return
    except json.JSONDecodeError:
        logging.error("Error decoding JSON. Please check the format of 'news_config.json'.")
        return

    news_queries = config.news_queries
    logging.info("Loaded news queries: %s", news_queries)

    for query in news_queries:
        articles = fetch_news_articles(api_key, query)
        sentiment_results = [perform_sentiment_analysis(article['content']) for article in articles]
        upload_to_mongodb(mongo_config, articles, sentiment_results)


if __name__ == "__main__":
    main()
