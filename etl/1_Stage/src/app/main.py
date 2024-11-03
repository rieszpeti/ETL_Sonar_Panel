import os
import logging
import psycopg2
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class PostgresConfig:
    dbname: str
    user: str
    password: str
    host: str
    port: int

    def __post_init__(self):
        # Check if any of the required fields are missing
        missing_fields = [
            field for field in ["dbname", "user", "password", "host", "port"]
            if getattr(self, field) is None
        ]
        if missing_fields:
            raise ValueError(f"Missing required database configuration fields: {', '.join(missing_fields)}")


def setup_logging():
    log_folder = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_folder, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(log_folder, 'app.log'))
        ]
    )


def connect_postgres(config: PostgresConfig):
    try:
        connection = psycopg2.connect(
            dbname=config.dbname,
            user=config.user,
            password=config.password,
            host=config.host,
            port=config.port,
        )
        logging.info(f"Connected to database: {config.dbname} at {config.host}")
        return connection
    except Exception as e:
        logging.error(f"Error connecting to PostgreSQL: {e}")
        return None


def truncate_table(cursor, table_name, cascade=False):
    """
    Truncate the specified table.

    Parameters:
    - cursor: The database cursor to execute the command.
    - table_name: The name of the table to truncate.
    - cascade: If True, use CASCADE to also truncate dependent tables.
    """
    try:
        # Construct the TRUNCATE command directly as a string
        cascade_clause = "CASCADE" if cascade else ""
        truncate_command = f"TRUNCATE TABLE stage.{table_name} {cascade_clause}".strip()

        cursor.execute(truncate_command)
        logging.info(f"Truncated table: {table_name}")
    except Exception as e:
        logging.error(f"Error truncating table {table_name}: {e}")
        cursor.connection.rollback()  # Rollback if there's an error


def copy_table_data(source_cursor, dest_cursor, table_name):
    """Copy data from source table to destination table."""
    source_cursor.execute(f"SELECT * FROM satellite_image_processing.{table_name}")
    rows = source_cursor.fetchall()

    if rows:
        # Construct insert query for destination table
        placeholders = ', '.join(['%s'] * len(rows[0]))
        insert_query = f"INSERT INTO stage.{table_name} VALUES ({placeholders})"

        dest_cursor.executemany(insert_query, rows)
        logging.info(f"Copied {len(rows)} rows to {table_name}")
    else:
        logging.info(f"No rows found in table: {table_name}")


def main():
    load_dotenv()
    setup_logging()

    source_config = PostgresConfig(
        dbname=os.getenv("SOURCE_DBNAME"),
        user=os.getenv("SOURCE_USER"),
        password=os.getenv("SOURCE_PASSWORD"),
        host=os.getenv("SOURCE_HOST"),
        port=int(os.getenv("SOURCE_PORT"))
    )

    dest_config = PostgresConfig(
        dbname=os.getenv("DEST_DBNAME"),
        user=os.getenv("DEST_USER"),
        password=os.getenv("DEST_PASSWORD"),
        host=os.getenv("DEST_HOST"),
        port=int(os.getenv("DEST_PORT"))
    )

    source_conn = connect_postgres(source_config)
    dest_conn = connect_postgres(dest_config)

    if not source_conn or not dest_conn:
        logging.error("Failed to connect to source or destination database.")
        return

    source_cursor = source_conn.cursor()
    dest_cursor = dest_conn.cursor()

    # Truncate destination tables
    dest_tables = [
        "images",
        "coordinates",
        "predictions_roof_type",
        "detection_solar_panel"
    ]

    for table in dest_tables:
        truncate_table(dest_cursor, table)

    # Copy data from source to destination
    source_tables = [
        "images",
        "coordinates",
        "predictions_roof_type",
        "detection_solar_panel"
    ]

    for table in source_tables:
        copy_table_data(source_cursor, dest_cursor, table)

    dest_conn.commit()
    logging.info("Data transfer completed successfully.")

    source_cursor.close()
    dest_cursor.close()
    source_conn.close()
    dest_conn.close()


if __name__ == "__main__":
    main()
