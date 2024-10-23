import requests
import logging
from typing import List, Dict
from datetime import datetime
from transformers import pipeline
from pymongo import MongoClient

from mongodb_config import MongoDBConfig


def fetch_news_articles(api_key: str, query: str) -> List[Dict[str, str]]:
    """Fetch news articles based on a given query term from the News API."""
    url = f'https://newsapi.org/v2/everything?q={query}&apiKey={api_key}'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        articles = []
        for article in data['articles']:
            articles.append({
                'title': article['title'],
                'content': article.get('content', 'No content available')
            })
        logging.info(f"Fetched {len(articles)} articles for query '{query}'.")
        return articles
    else:
        logging.error("Error fetching articles: %s %s", response.status_code, response.text)
        return []


def perform_sentiment_analysis(content: str) -> Dict[str, float]:
    """Perform sentiment analysis on the given content."""
    sentiment_pipeline = pipeline(
        "text-classification", model="mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis")
    result = sentiment_pipeline(content)
    return result[0]  # Return the first result


def upload_to_mongodb(dbconfig: MongoDBConfig,
                      articles: List[Dict[str, str]],
                      sentiment_results: List[Dict[str, float]]):
    """Upload articles and their sentiment results to MongoDB."""
    client = MongoClient(dbconfig.connection_string)
    db = client[dbconfig.db_name]
    collection = db[dbconfig.collection_name]

    current_date = datetime.now().strftime("%Y-%m-%d") 
    logging.info("Current date: %s", current_date) 


    for article, sentiment in zip(articles, sentiment_results):
        if collection.find_one({"title": article['title']}):
            logging.info("Article already exists in the database: %s", article['title'])
            continue

        data = {
            'title': article['title'],
            'content': article['content'],
            'sentiment_label': sentiment['label'],
            'sentiment_score': sentiment['score'],
            'date_fetched': current_date
        }
        collection.insert_one(data)
        logging.info("Inserted article: %s", article['title'])

    client.close()
