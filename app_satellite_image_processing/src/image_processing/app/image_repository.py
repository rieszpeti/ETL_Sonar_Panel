import os
import logging
import psycopg2
from dataclasses import dataclass

# Ensure you have a logger configured
logger = logging.getLogger(__name__)


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


class ImageRepository:
    def __init__(self, config: PostgresConfig):
        self.connection = self.create_connection(config)
        self.cursor = self.connection.cursor()

    def create_connection(self, config: PostgresConfig):
        """Establish a connection to the PostgreSQL database."""
        try:
            connection = psycopg2.connect(
                dbname=config.dbname,
                user=config.user,
                password=config.password,
                host=config.host,
                port=config.port,
            )
            logger.info("PostgreSQL connection established.")
            return connection
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            raise

    def has_predictions(self, image_id: int) -> bool:
        """Check if there are existing predictions for the given image ID."""
        query = "SELECT COUNT(*) FROM satellite_image_processing.predictions_roof_type WHERE image_id = %s;"
        with self.connection.cursor() as cursor:
            cursor.execute(query, (image_id,))
            count = cursor.fetchone()[0]
        return count > 0

    def has_detections(self, image_id: int) -> bool:
        """Check if there are existing detections for the given image ID."""
        query = "SELECT COUNT(*) FROM satellite_image_processing.detection_solar_panel WHERE image_id = %s;"
        with self.connection.cursor() as cursor:
            cursor.execute(query, (image_id,))
            count = cursor.fetchone()[0]
        return count > 0

    # Images Table Methods
    def insert_image(self, width: int, height: int, filename: str, image_data: bytes):
        query = """
        INSERT INTO satellite_image_processing.images (width, height, filename, image_data)
        VALUES (%s, %s, %s, %s)
        RETURNING image_id;
        """
        params = (width, height, filename, image_data)
        try:
            self.cursor.execute(query, params)
            image_id = self.cursor.fetchone()[0]
            self.connection.commit()
            logger.info(f"Inserted image with ID: {image_id}")
            return image_id
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error inserting image: {e}")
            return None

    def fetch_image(self, image_id: int):
        query = "SELECT * FROM satellite_image_processing.images WHERE image_id = %s;"
        self.cursor.execute(query, (image_id,))
        return self.cursor.fetchone()

    def fetch_all_images(self):
        query = "SELECT * FROM satellite_image_processing.images;"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def delete_image(self, image_id: int):
        query = "DELETE FROM satellite_image_processing.images WHERE image_id = %s;"
        self.cursor.execute(query, (image_id,))
        self.connection.commit()

    def get_image_by_filename(self, filename: str):
        """Fetch an image by its filename."""
        query = "SELECT * FROM satellite_image_processing.images WHERE filename = %s;"
        self.cursor.execute(query, (filename,))
        result = self.cursor.fetchone()
        if result:
            logger.info(f"Fetched image with filename: {filename}")
        else:
            logger.info(f"No image found with filename: {filename}")
        return result

    # Coordinates Table Methods
    def insert_coordinate(self, image_id: int, latitude: float, longitude: float):
        query = """
        INSERT INTO satellite_image_processing.coordinates (image_id, latitude, longitude)
        VALUES (%s, %s, %s)
        RETURNING coordinates_id;
        """
        params = (image_id, latitude, longitude)
        try:
            self.cursor.execute(query, params)
            coordinates_id = self.cursor.fetchone()[0]
            self.connection.commit()
            logger.info(f"Inserted coordinates with ID: {coordinates_id}")
            return coordinates_id
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error inserting coordinates: {e}")
            return None

    # Predictions Roof Type Methods
    def insert_prediction_roof_type(self, image_id: int, class_name: str, time_taken: float, confidence: float,
                                    prediction_type: str):
        query = """
        INSERT INTO satellite_image_processing.predictions_roof_type (image_id, class_name, time_taken, confidence, prediction_type)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING prediction_id;
        """
        params = (image_id, class_name, time_taken, confidence, prediction_type)
        try:
            self.cursor.execute(query, params)
            prediction_id = self.cursor.fetchone()[0]
            self.connection.commit()
            logger.info(f"Inserted roof type prediction with ID: {prediction_id}")
            return prediction_id
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error inserting roof type prediction: {e}")
            return None

    # Detection Solar Panel Methods
    def insert_detection_solar_panel(self, image_id: int, class_name: str, confidence: float, x: float, y: float,
                                     width: float, height: float, image_data: bytes):
        query = """
        INSERT INTO satellite_image_processing.detection_solar_panel (image_id, class_name, confidence, x, y, width, height, image_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING detection_id;
        """
        params = (image_id, class_name, confidence, x, y, width, height, image_data)
        try:
            self.cursor.execute(query, params)
            detection_id = self.cursor.fetchone()[0]
            self.connection.commit()
            logger.info(f"Inserted solar panel detection with ID: {detection_id}")
            return detection_id
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error inserting solar panel detection: {e}")
            return None

    def get_first_coordinate_by_image_id(self, image_id: int):
        """Fetch the first coordinate by image ID."""
        query = "SELECT * FROM satellite_image_processing.coordinates WHERE image_id = %s LIMIT 1;"
        self.cursor.execute(query, (image_id,))
        return self.cursor.fetchone()

    def insert_no_predictions(self, image_id: int):
        """Insert a placeholder entry indicating no predictions for the given image ID."""
        query = """
        INSERT INTO satellite_image_processing.detection_solar_panel (image_id, class_name, confidence, x, y, width, height, image_data)
        VALUES (%s, 'No predictions', 0, 0, 0, 0, 0, NULL);
        """
        params = (image_id,)
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            logger.info(f"Inserted placeholder for no predictions for image_id: {image_id}")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error inserting placeholder for no predictions: {e}")

    def close_connection(self):
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("PostgreSQL connection closed.")
