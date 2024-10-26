import psycopg2
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import logging

from logging_config import setup_logging

load_dotenv()
logger = logging.getLogger("news")

def connect_to_mongodb():
    """Connects to MongoDB and returns the collection."""
    mongo_uri = os.getenv("MONGO_URI")
    mongo_db_name = os.getenv("MONGO_DB_NAME_NEWS")
    mongo_collection_name = os.getenv("MONGO_COLLECTION_NAME_NEWS")

    logging.info("Connecting to MongoDB...")
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client[mongo_db_name]
    mongo_collection = mongo_db[mongo_collection_name]
    logging.info("Successfully connected to MongoDB.")
    return mongo_collection


def connect_to_postgres():
    """Connects to PostgreSQL and returns the connection and cursor."""
    logging.info("Connecting to PostgreSQL...")
    pg_conn = psycopg2.connect(
        dbname=os.getenv("PG_DBNAME"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT")
    )
    logging.info("Successfully connected to PostgreSQL.")
    return pg_conn, pg_conn.cursor()


def load_sentiment_data(mongo_collection, pg_cursor):
    """Loads sentiment data from MongoDB into PostgreSQL."""
    logging.info("Loading sentiment data from MongoDB...")

    for doc in mongo_collection.find():
        oid = str(doc.get('_id'))
        title = doc.get('title')
        content = doc.get('content')
        sentiment_label = doc.get('sentiment_label')
        sentiment_score = doc.get('sentiment_score')
        date_fetched = doc.get('date_fetched')

        insert_query = """
        INSERT INTO star.sentiment (oid, title, content, label, score, date_fetched)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (oid) DO NOTHING;  
        """
        # Execute the insert with all necessary fields
        pg_cursor.execute(insert_query,
                          (oid, title, content, sentiment_label, sentiment_score, date_fetched))
        logging.info(f"Inserted sentiment data for OID: {oid}")

    logging.info("Data loading complete.")


def main():
    try:
        mongo_collection = connect_to_mongodb()

        pg_conn, pg_cursor = connect_to_postgres()

        load_sentiment_data(mongo_collection, pg_cursor)

        pg_conn.commit()
        logging.info("Transaction committed successfully.")
    except Exception as e:
        logging.error("An error occurred during migration: %s", e)
    finally:
        if 'pg_cursor' in locals():
            pg_cursor.close()
            logging.info("PostgreSQL cursor closed.")
        if 'pg_conn' in locals():
            pg_conn.close()
            logging.info("PostgreSQL connection closed.")
        logging.info("Migration process finished.")


if __name__ == "__main__":
    setup_logging()
    main()
