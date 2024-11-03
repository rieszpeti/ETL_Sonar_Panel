import os
import psycopg2
from psycopg2 import sql
import psycopg2.extras
import logging
from dataclasses import dataclass
from dotenv import load_dotenv
from datetime import datetime, timedelta


@dataclass
class PostgresConfig:
    dbname: str
    user: str
    password: str
    host: str
    port: int

    def __post_init__(self):
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


def get_date_id(tz_timestamp, cursor):
    """Retrieve date_id from dim_date based on a TIMESTAMPTZ value."""
    query = sql.SQL("""
        SELECT date_id
        FROM star.dim_date
        WHERE date = %s::DATE;
    """)

    cursor.execute(query, (tz_timestamp,))

    result = cursor.fetchone()

    if result:
        return result[0]
    else:
        return None


def connect_to_db(config: PostgresConfig):
    try:
        logging.info(f"Connecting to {config.dbname} database at {config.host}...")
        conn = psycopg2.connect(
            dbname=config.dbname,
            user=config.user,
            password=config.password,
            host=config.host,
            port=config.port
        )
        logging.info(f"Connected to {config.dbname} database successfully.")
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to {config.dbname} database: {e}")
        raise


def populate_dim_date(start_year=2020, end_year=2025, conn=None):
    """Populate the dim_date table with dates from start_year to end_year."""
    if conn is None:
        raise ValueError("A valid database connection is required.")

    with conn.cursor() as cursor:
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        current_date = start_date

        logging.info(f"Populating dim_date table from {start_year} to {end_year}.")

        while current_date <= end_date:
            year = current_date.year
            month = current_date.month
            day = current_date.day
            week = current_date.isocalendar()[1]
            quarter = (month - 1) // 3 + 1

            # Create date_id in the format YYYYMMDD
            date_id = current_date.strftime("%Y%m%d")

            cursor.execute(
                """
                INSERT INTO star.dim_date (date_id, date, year, month, day, week, quarter)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (date) DO NOTHING;
                """,
                (date_id, current_date, year, month, day, week, quarter)
            )
            current_date += timedelta(days=1)

        conn.commit()
        logging.info("dim_date table population completed.")


def get_primary_key_by_field(cursor, schema_name, table_name, primary_key_column, field_name, field_value):
    cursor.execute(
    f"""
        SELECT {primary_key_column}
        FROM {schema_name}.{table_name}
        WHERE {field_name} = %s;
    """, (field_value,))
    result = cursor.fetchone()
    return result[0] if result else None


def transfer_images_and_coordinates(history_cursor, star_cursor):
    """Transfer data from history.images and history.coordinates to star.dim_images."""
    logging.info("Transferring data to star.dim_images...")

    # Select image data along with latitude and longitude where valid_to is NULL in both tables
    history_cursor.execute(
        """
        SELECT i.image_id, i.width, i.height, i.filename, c.latitude, c.longitude
        FROM history.images AS i
        JOIN history.coordinates AS c ON i.image_id = c.image_id
        WHERE i.valid_to IS NULL AND c.valid_to IS NULL;
        """
    )
    images = history_cursor.fetchall()

    # Insert into star.dim_images with latitude and longitude
    for image in images:
        star_cursor.execute(
            """
            INSERT INTO star.dim_images (image_id, width, height, filename, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (image_id) DO NOTHING;
            """,
            image
        )
    logging.info("Data transfer to star.dim_images completed.")


def transfer_predictions(history_cursor, star_cursor):
    """Transfer data from history.predictions_roof_type to star.dim_predictions_roof_type."""
    logging.info("Transferring data to star.dim_predictions_roof_type...")

    history_cursor.execute(
        """
        SELECT prediction_id, class_name, time_taken, confidence, prediction_type, date_processed 
        FROM history.predictions_roof_type
        WHERE valid_to IS NULL;
        """
    )
    predictions = history_cursor.fetchall()

    for pred in predictions:
        star_cursor.execute(
            """
            INSERT INTO star.dim_predictions_roof_type 
            (prediction_id, class_name, time_taken, confidence, prediction_type, date_processed) 
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (prediction_id) DO NOTHING;
            """,
            pred
        )
    logging.info("Data transfer to star.dim_predictions_roof_type completed.")


def transfer_detections(history_cursor, star_cursor):
    """Transfer data from history.detection_solar_panel to star.dim_detections_solar_panel."""
    logging.info("Transferring data to star.dim_detections_solar_panel...")

    history_cursor.execute(
        """
        SELECT detection_id, class_name, confidence, x, y, width, height, image_data, date_processed 
        FROM history.detection_solar_panel
        WHERE valid_to IS NULL;
        """
    )
    detections = history_cursor.fetchall()

    for detection in detections:
        star_cursor.execute(
            """
            INSERT INTO star.dim_detections_solar_panel (detection_id, class_name, confidence, x, y, width, height, image_data, date_processed) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (detection_id) DO NOTHING;
            """,
            detection
        )
    logging.info("Data transfer to star.dim_detections_solar_panel completed.")


def populate_fact_table(history_cursor, star_cursor):
    logging.info("Transferring data to star.dim_images...")
    history_cursor.execute(
        """
            SELECT
                i.image_id,
                i.date_uploaded,
                pr.prediction_id,
                dsp.detection_id
            FROM
                history.images AS i
            LEFT JOIN
                history.predictions_roof_type AS pr
                ON i.image_id = pr.image_id
                AND pr.valid_to IS NULL
            LEFT JOIN
                history.detection_solar_panel AS dsp
                ON i.image_id = dsp.image_id
                AND dsp.valid_to IS NULL
            WHERE
                i.valid_to IS NULL;
        """)
    images = history_cursor.fetchall()

    for image in images:
        image_id = get_primary_key_by_field(
            star_cursor,
            schema_name='star',
            table_name='dim_images',
            primary_key_column='dim_image_id',
            field_name='image_id',
            field_value=image[0])
        dim_roof_type_id = get_primary_key_by_field(
            star_cursor,
            schema_name='star',
            table_name='dim_predictions_roof_type',
            primary_key_column='dim_roof_type_id',
            field_name='prediction_id',
            field_value=image[2])
        dim_solar_panel_id = get_primary_key_by_field(
            star_cursor,
            schema_name='star',
            table_name='dim_detections_solar_panel',
            primary_key_column='dim_solar_panel_id',
            field_name='detection_id',
            field_value=image[3])

        image_upload_date = image[1]
        date_id = get_date_id(image_upload_date, star_cursor)

        # Prepare the SQL insert statement
        insert_sql = """
            INSERT INTO star.fact_images (
                image_id,
                dim_roof_type_id,
                dim_solar_panel_id,
                date_id,
                image_date_uploaded
            ) VALUES (%s, %s, %s, %s, %s);
            """

        # Execute the insert statement using a cursor
        star_cursor.execute(insert_sql, (
            image_id,
            dim_roof_type_id,
            dim_solar_panel_id,
            date_id,
            image_upload_date
        ))

    logging.info("Transferring data to star.fact_images...")


def transfer_data(history_conn, star_conn):
    with history_conn.cursor() as history_cursor, star_conn.cursor() as star_cursor:
        logging.info("Transferring data to star.dim_images...")

        transfer_images_and_coordinates(history_cursor, star_cursor)
        transfer_predictions(history_cursor, star_cursor)
        transfer_detections(history_cursor, star_cursor)
        star_conn.commit()
        logging.info("Dimension table transfers completed successfully.")

        populate_fact_table(history_cursor, star_cursor)

    star_conn.commit()
    logging.info("Data transfer completed successfully.")


def truncate_table(cursor, table_name, cascade=True):
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
        truncate_command = f"TRUNCATE TABLE star.{table_name} {cascade_clause}".strip()

        cursor.execute(truncate_command)
        logging.info(f"Truncated table: {table_name}")
    except Exception as e:
        logging.error(f"Error truncating table {table_name}: {e}")
        cursor.connection.rollback()  # Rollback if there's an error


def main():
    setup_logging()
    load_dotenv()

    history_config = PostgresConfig(
        dbname=os.getenv("SOURCE_DBNAME"),
        user=os.getenv("SOURCE_USER"),
        password=os.getenv("SOURCE_PASSWORD"),
        host=os.getenv("SOURCE_HOST"),
        port=int(os.getenv("SOURCE_PORT"))
    )

    star_config = PostgresConfig(
        dbname=os.getenv("DEST_DBNAME"),
        user=os.getenv("DEST_USER"),
        password=os.getenv("DEST_PASSWORD"),
        host=os.getenv("DEST_HOST"),
        port=int(os.getenv("DEST_PORT"))
    )

    history_conn = connect_to_db(history_config)
    star_conn = connect_to_db(star_config)

    try:
        with star_conn.cursor() as cursor:
            tables_to_truncate = [
                "dim_images",
                "dim_predictions_roof_type",
                "dim_detections_solar_panel",
                "fact_images"
            ]
            for table in tables_to_truncate:
                truncate_table(cursor, table, cascade=True)

            star_conn.commit()

        populate_dim_date(2020, 2025, star_conn)
        transfer_data(history_conn, star_conn)
    except Exception as e:
        logging.error(f"Error during data transfer: {e}")
    finally:
        history_conn.close()
        star_conn.close()
        logging.info("Database connections closed.")


if __name__ == '__main__':
    main()
