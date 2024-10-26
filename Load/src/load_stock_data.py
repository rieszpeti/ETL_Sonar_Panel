import os

import psycopg2
import logging

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


def load_stock_data(source_conn, target_conn):
    try:
        stock_datas = []

        with source_conn.cursor() as cursor:
            cursor.execute("""
                SELECT * 
                FROM stock.stock_data;
            """)

            stock_datas = cursor.fetchall()

        logger.info(f"Successfully loaded {len(stock_datas)} stock records.")
        for stock_data in stock_datas:
            with target_conn.cursor() as target_cursor:
                target_cursor.execute("""
                    INSERT INTO star.stock_data ("date", symbol, price)
                    VALUES (%s, %s, %s);
                """, (stock_data[0], stock_data[1], stock_data[2]))

            target_conn.commit()

    except Exception as e:
        logger.error(f"Error loading stock data: {e}")
        target_conn.rollback()


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
    main()
