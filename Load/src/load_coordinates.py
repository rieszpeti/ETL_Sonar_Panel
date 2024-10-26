import psycopg2
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import logging
import random

from logging_config import setup_logging

load_dotenv()
logger = logging.getLogger("news")



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


def load_image_coordinates(pg_cursor):
    """Generates and loads dummy coordinates for images in PostgreSQL."""
    logging.info("Generating and loading dummy coordinates for images...")

    # Assuming you have some images already in the images table
    pg_cursor.execute("SELECT image_id FROM star.images;")
    image_ids = pg_cursor.fetchall()

    for image_id in image_ids:
        latitude = random.uniform(45.735, 46.879)  # Latitude range for Hungary
        longitude = random.uniform(16.162, 19.646)  # Longitude range for Hungary

        insert_query = """
        INSERT INTO star.coordinates (image_id, latitude, longitude)
        VALUES (%s, %s, %s);
        """
        pg_cursor.execute(insert_query, (image_id[0], latitude, longitude))
        logging.info(f"Inserted coordinates for image ID: {image_id[0]} (Lat: {latitude}, Lon: {longitude})")

    logging.info("Coordinates loading complete.")


def main():
    try:
        pg_conn, pg_cursor = connect_to_postgres()

        load_image_coordinates(pg_cursor)

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
