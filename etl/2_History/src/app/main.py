import os
import logging
import psycopg2
from dataclasses import dataclass
from dotenv import load_dotenv
from datetime import datetime


@dataclass
class PostgresConfig:
    dbname: str
    user: str
    password: str
    host: str
    port: int

    def __post_init__(self):
        missing_fields = [field for field in ["dbname", "user", "password", "host", "port"]
                          if getattr(self, field) is None]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


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


def load_config(env_prefix: str) -> PostgresConfig:
    return PostgresConfig(
        dbname=os.getenv(f"{env_prefix}_DBNAME"),
        user=os.getenv(f"{env_prefix}_USER"),
        password=os.getenv(f"{env_prefix}_PASSWORD"),
        host=os.getenv(f"{env_prefix}_HOST"),
        port=int(os.getenv(f"{env_prefix}_PORT", 5432))
    )


def initialize_connection(config: PostgresConfig):
    try:
        return psycopg2.connect(
            dbname=config.dbname,
            user=config.user,
            password=config.password,
            host=config.host,
            port=config.port
        )
    except psycopg2.Error as e:
        logging.error(f"Failed to connect to database: {e}")
        raise


def transfer_data(stage_conn, history_conn):
    with stage_conn.cursor() as stage_cursor, history_conn.cursor() as history_cursor:
        # Process images
        stage_cursor.execute("SELECT * FROM stage.images;")
        rows = stage_cursor.fetchall()
        for row in rows:
            image_id = row[0]
            width = row[1]
            height = row[2]
            filename = row[3]
            image_data = row[4]
            date_uploaded = row[5]

            # Step 1: Check for existing records in the history table
            history_cursor.execute("""
                SELECT * FROM history.images WHERE image_id = %s AND valid_to IS NULL;
            """, (image_id,))
            current_record = history_cursor.fetchone()

            if current_record:
                # Step 2: Update existing record to mark as historical
                history_cursor.execute("""
                    UPDATE history.images
                    SET valid_to = %s
                    WHERE image_id = %s AND valid_to IS NULL;
                """, (datetime.now(), image_id))

            # Step 3: Insert the new record
            history_cursor.execute("""
                INSERT INTO history.images (image_id, width, height, filename, image_data, date_uploaded, valid_from, valid_to)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NULL);
            """, (image_id, width, height, filename, image_data, date_uploaded, datetime.now()))

        logging.info(f"Transferred {len(rows)} rows from images to history.")

        # Process coordinates
        stage_cursor.execute("SELECT * FROM stage.coordinates;")
        rows = stage_cursor.fetchall()
        for row in rows:
            coordinates_id = row[0]
            image_id = row[1]
            latitude = row[2]
            longitude = row[3]

            history_cursor.execute("""
                SELECT * FROM history.coordinates WHERE image_id = %s AND valid_to IS NULL;
            """, (image_id,))
            current_record = history_cursor.fetchone()

            if current_record:
                history_cursor.execute("""
                    UPDATE history.coordinates
                    SET valid_to = %s
                    WHERE image_id = %s AND valid_to IS NULL;
                """, (datetime.now(), image_id))

            history_cursor.execute("""
                INSERT INTO history.coordinates (coordinates_id, image_id, latitude, longitude, valid_from, valid_to)
                VALUES (%s, %s, %s, %s, %s, NULL);
            """, (coordinates_id, image_id, latitude, longitude, datetime.now()))

        logging.info(f"Transferred {len(rows)} rows from coordinates to history.")

        # Process predictions_roof_type
        stage_cursor.execute("SELECT * FROM stage.predictions_roof_type;")
        rows = stage_cursor.fetchall()
        for row in rows:
            prediction_id = row[0]
            image_id = row[1]
            class_name = row[2]
            time_taken = row[3]
            confidence = row[4]
            prediction_type = row[5]
            date_processed = row[6]

            history_cursor.execute("""
                SELECT * FROM history.predictions_roof_type WHERE prediction_id = %s AND valid_to IS NULL;
            """, (prediction_id,))
            current_record = history_cursor.fetchone()

            if current_record:
                history_cursor.execute("""
                    UPDATE history.predictions_roof_type
                    SET valid_to = %s
                    WHERE prediction_id = %s AND valid_to IS NULL;
                """, (datetime.now(), prediction_id))

            history_cursor.execute("""
                INSERT INTO history.predictions_roof_type (prediction_id, image_id, class_name, time_taken, confidence, prediction_type, date_processed, valid_from, valid_to)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL);
            """, (prediction_id, image_id, class_name, time_taken, confidence, prediction_type, date_processed, datetime.now()))

        logging.info(f"Transferred {len(rows)} rows from predictions_roof_type to history.")

        # Process detection_solar_panel
        stage_cursor.execute("SELECT * FROM stage.detection_solar_panel;")
        rows = stage_cursor.fetchall()
        for row in rows:
            detection_id = row[0]
            image_id = row[1]
            class_name = row[2]
            confidence = row[3]
            x = int(float(row[4]))  # Convert to integer if necessary
            y = int(float(row[5]))
            width = int(float(row[6]))
            height = int(float(row[7]))
            image_data = row[8]
            date_processed = row[9]

            history_cursor.execute("""
                SELECT * FROM history.detection_solar_panel WHERE detection_id = %s AND valid_to IS NULL;
            """, (detection_id,))
            current_record = history_cursor.fetchone()

            if current_record:
                history_cursor.execute("""
                    UPDATE history.detection_solar_panel
                    SET valid_to = %s
                    WHERE detection_id = %s AND valid_to IS NULL;
                """, (datetime.now(), detection_id))

            history_cursor.execute("""
                INSERT INTO history.detection_solar_panel (detection_id, image_id, class_name, confidence, x, y, width, height, image_data, date_processed, valid_from, valid_to)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL);
            """, (detection_id, image_id, class_name, confidence, x, y, width, height, image_data, date_processed, datetime.now()))

        logging.info(f"Transferred {len(rows)} rows from detection_solar_panel to history.")

        history_conn.commit()
        logging.info("Data transfer committed.")


def main():
    setup_logging()
    load_dotenv()

    try:
        source_config = load_config("SOURCE")
        dest_config = load_config("DEST")

        with initialize_connection(source_config) as stage_conn, initialize_connection(dest_config) as history_conn:
            transfer_data(stage_conn, history_conn)
            logging.info("Data transfer completed successfully.")
    except Exception as e:
        logging.error(f"Data transfer failed: {e}")


if __name__ == '__main__':
    main()
