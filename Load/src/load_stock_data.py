import os

import psycopg2
import logging

from dotenv import load_dotenv

from logging_config import setup_logging

logger = logging.getLogger("stock_data")

load_dotenv()


def connect_postgresql(db_name="PG_DBNAME", host="PG_HOST", port="PG_PORT"):
    """Connect to the PostgreSQL database."""
    try:
        connection = psycopg2.connect(
            dbname=os.getenv(db_name),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv(host),
            port=os.getenv(port),
        )
        logger.info("PostgreSQL connection successful.")
        return connection
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        return None


def fetch_stock_data(source_conn):
    """Generator to fetch stock data from the source database."""
    try:
        with source_conn.cursor() as cursor:
            cursor.execute("""SELECT * FROM stock.stock_data;""")
            while True:
                stock_data = cursor.fetchone()
                if stock_data is None:
                    break
                yield stock_data
                logger.info(f"Fetched stock record: {stock_data}")
    except Exception as e:
        logger.error(f"Error fetching stock data: {e}")


def insert_stock_data(target_conn, stock_data):
    """Insert a single stock data record into the target database."""
    try:
        with target_conn.cursor() as target_cursor:
            target_cursor.execute(""" 
                INSERT INTO star.stock_data ("date", symbol, price)
                VALUES (%s, %s, %s)
                ON CONFLICT (date, symbol) DO NOTHING;
            """, (stock_data[0], stock_data[1], stock_data[2]))

        target_conn.commit()
        logger.info(f"Inserted stock record: {stock_data}")
    except Exception as e:
        logger.error(f"Error inserting stock data: {e}")
        target_conn.rollback()


def load_stock_data(source_conn, target_conn):
    """Load stock data from source to target database."""
    stock_generator = fetch_stock_data(source_conn)
    for stock_data in stock_generator:
        insert_stock_data(target_conn, stock_data)


def main():
    source_conn = connect_postgresql(
        db_name="PG_DBNAME_SOURCE", host="PG_HOST_SOURCE", port="PG_PORT_SOURCE")
    target_conn = connect_postgresql()

    if source_conn and target_conn:
        load_stock_data(source_conn, target_conn)

    if source_conn:
        source_conn.close()
    if target_conn:
        target_conn.close()

    logger.info("PostgreSQL connection closed.")


if __name__ == '__main__':
    setup_logging()
    main()
