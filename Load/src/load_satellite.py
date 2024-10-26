import psycopg2
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def connect_to_mongodb():
    """Connects to MongoDB and returns the collection."""
    mongo_uri = os.getenv("MONGO_URI")
    mongo_db_name = os.getenv("MONGO_DB_NAME_SATELLITE")
    mongo_collection_name = os.getenv("MONGO_COLLECTION_NAME_SATELLITE")

    logging.info("Connecting to MongoDB...")
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client[mongo_db_name]
    mongo_collection = mongo_db[mongo_collection_name]
    logging.info("Successfully connected to MongoDB.")
    return mongo_collection


def connect_postgresql():
    """Connect to the PostgreSQL database."""
    try:
        connection = psycopg2.connect(
            dbname=os.getenv("PG_DBNAME"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT"),
        )
        logger.info("PostgreSQL connection successful.")
        return connection
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        return None


def insert_image(connection, width, height, filename):
    """Insert an image record into the images table."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO star.images (width, height, filename)
                VALUES (%s, %s, %s) RETURNING image_id;
            """, (width, height, filename))
            image_id = cursor.fetchone()[0]
            connection.commit()
            logger.info(f"Inserted image with ID: {image_id}")
            return image_id
    except Exception as e:
        logger.error(f"Error inserting image: {e}")
        return None


def insert_prediction(connection, image_id, class_name, time_taken, confidence, prediction_type):
    """Insert a prediction record into the predictions table."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO star.predictions_roof_type (image_id, class_name, time_taken, confidence, prediction_type)
                VALUES (%s, %s, %s, %s, %s) RETURNING prediction_id;
            """, (image_id, class_name, time_taken, confidence, prediction_type))
            prediction_id = cursor.fetchone()[0]
            connection.commit()
            logger.info(f"Inserted prediction with ID: {prediction_id} for image ID: {image_id}")
            return prediction_id
    except Exception as e:
        logger.error(f"Error inserting prediction: {e}")
        return None


def insert_detection(connection, image_id, class_name, confidence, x, y, width, height, detected_image_name):
    """Insert a detection record into the detection table."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO star.detection_solar_panel (image_id, class_name, confidence, x, y, width, height, detected_image_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING detection_id;
            """, (image_id, class_name, confidence, x, y, width, height, detected_image_name))
            detection_id = cursor.fetchone()[0]
            connection.commit()
            logger.info(f"Inserted detection with ID: {detection_id} for image ID: {image_id}")
            return detection_id
    except Exception as e:
        logger.error(f"Error inserting detection: {e}")
        return None


def check_if_processed(document):
    """Check if the document has been processed."""
    processed = document.get('processed') is True
    logger.debug(f"Document with ID {document['_id']} processed status: {processed}")
    return processed


def find_pair_by_filename(original_filename, collection, original_doc_id):
    """Finds a paired document in the collection based on the image_path, excluding the original document."""
    logger.info(f"Finding paired document for filename: {original_filename}")

    for document in collection.find():
        filename = get_filename(document)

        if document.get("_id") == original_doc_id:  # found itself
            logger.info("Found paired document is the same as original")
            continue

        if filename == original_filename:
            logger.info("Found paired document is the same as original")
            return document

    return None


def get_detection_or_roof_type_prediction(doc1, doc2):
    """Determine which document is for solar panels and which is for roof type."""
    solar_panel_prediction = None
    roof_type_prediction = None

    if doc1.get("prediction_type") == "solar-panels-81zxz":
        solar_panel_prediction = doc1
    elif doc1.get("prediction_type") == "roof-type-classifier-bafod":
        roof_type_prediction = doc1

    if doc2 and doc2.get("prediction_type") == "solar-panels-81zxz":
        solar_panel_prediction = doc2
    elif doc2 and doc2.get("prediction_type") == "roof-type-classifier-bafod":
        roof_type_prediction = doc2

    logger.info("Detection and roof type prediction retrieval complete.")
    return solar_panel_prediction, roof_type_prediction


def get_image_id_by_name(connection, filename):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT image_id 
                FROM star.images
                WHERE filename = %s; 
            """, (filename,))

            image_id = cursor.fetchone()
            if image_id:
                logger.info(f"Found image with ID: {image_id[0]}")
                return image_id[0]
            else:
                logger.warning(f"No image found with name: {filename}")
                return None
    except Exception as e:
        logger.error(f"Error retrieving image ID: {e}")
        return None


def insert_image_if_not_exists(connection, width, height, filename):
    image_id = get_image_id_by_name(connection, filename)
    if image_id:
        logger.info(f"Image already exists with ID: {image_id}")
        return image_id
    else:
        logger.info(f"Inserting new image: {filename}")
        return insert_image(connection, width, height, filename)


def get_image_name(image_path):
    image_name = image_path.split('/')[-1] if image_path else "unknown_image"
    logger.debug(f"Extracted image name: {image_name}")
    return image_name


def process_solar_detection(postgresql, image_id, solar_detection_doc):
    """Process solar detection predictions and insert them into the database."""
    if solar_detection_doc:
        logger.info(f"Processing solar detection document for image ID: {image_id}")
        for prediction in solar_detection_doc.get("predictions", []):
            class_name = prediction.get("class", "Unknown")
            confidence = prediction.get("confidence", 0)
            x = prediction.get("x", 0)  # Correctly fetch x
            y = prediction.get("y", 0)  # Correctly fetch y
            width = prediction.get("width", 0)  # Correctly fetch width
            height = prediction.get("height", 0)  # Correctly fetch height
            image_path = prediction.get("image_path")

            detected_image_name = get_image_name(image_path)

            insert_detection(
                postgresql, image_id, class_name, confidence, x, y, width, height, detected_image_name)


def process_roof_type_prediction(postgresql, image_id, roof_type_prediction):
    """Process roof type predictions and insert them into the database."""
    prediction = roof_type_prediction.get("predictions", [])

    if prediction:
        prediction = prediction[0]
        logger.info(f"Processing roof type prediction for image ID: {image_id}")

        time_taken = prediction.get("time")
        prediction_type = prediction.get("prediction_type")

        class_predictions = prediction.get("predictions", {})
        for class_name, details in class_predictions.items():
            confidence = details.get("confidence")
            insert_prediction(postgresql, image_id, class_name, time_taken, confidence, prediction_type)


def append_processed_to_document(collection, document):
    """Mark the document as processed in MongoDB."""
    result = collection.update_one(
        {'_id': document['_id']},
        {'$set': {'processed': True}}
    )

    if result.modified_count > 0:
        logger.info(f"Document with ID {document['_id']} updated successfully.")
    else:
        logger.warning(f"No document found with ID {document['_id']}.")


def find_value(data, target_key):
    """Recursively search for a target key in a nested dictionary and return its value."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                return value
            # If the value is a dictionary, search it recursively
            elif isinstance(value, dict):
                found_value = find_value(value, target_key)
                if found_value is not None:
                    return found_value
            # If the value is a list, search each item
            elif isinstance(value, list):
                for item in value:
                    found_value = find_value(item, target_key)
                    if found_value is not None:
                        return found_value
    return None


def get_filename(document):
    prediction_type = document.get("prediction_type")
    filename = (document.get("filename", "")
                .replace(prediction_type, "")
                .lstrip('_'))
    return filename


def remove_processed(collection):
    """Remove the 'processed' field from documents in the collection."""
    try:
        result = collection.update_many(
            {"processed": True},
            {"$unset": {"processed": ""}}
        )
        logger.info(f"Removed 'processed' field from {result.modified_count} documents.")
    except Exception as e:
        logger.error(f"Error removing 'processed' field: {e}")


def truncate_tables(connection):
    """Truncate specified tables in the star schema with CASCADE and restart their identities."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("BEGIN;")
            cursor.execute("TRUNCATE TABLE star.images CASCADE;")
            cursor.execute("TRUNCATE TABLE star.predictions_roof_type CASCADE;")
            cursor.execute("TRUNCATE TABLE star.detection_solar_panel CASCADE;")

            # Restart identities
            cursor.execute("ALTER SEQUENCE star.images_image_id_seq RESTART WITH 1;")
            cursor.execute("ALTER SEQUENCE star.predictions_roof_type_prediction_id_seq RESTART WITH 1;")
            cursor.execute("ALTER SEQUENCE star.detection_solar_panel_detection_id_seq RESTART WITH 1;")

            cursor.execute("COMMIT;")
            logger.info("Successfully truncated tables with CASCADE and reset identities in the star schema.")
    except Exception as e:
        logger.error(f"Error truncating tables or resetting identities: {e}")
        connection.rollback()


def main():
    collection = connect_to_mongodb()
    postgresql = connect_postgresql()

    if os.getenv("ENVIRONMENT") == "DEBUG":
        remove_processed(collection)
        truncate_tables(postgresql)

    if collection is not None and postgresql is not None:
        for document in collection.find():
            logger.info(f"Processing document with ID: {document['_id']}")
            filename = get_filename(document)
            paired_doc = find_pair_by_filename(filename, collection, document.get('_id'))
            solar_detection_doc, roof_type_doc = get_detection_or_roof_type_prediction(document, paired_doc)

            if not solar_detection_doc and not roof_type_doc:
                logger.warning("No predictions found, skipping document.")
                continue

            image_id = insert_image_if_not_exists(postgresql,
                                                  solar_detection_doc.get("image", {}).get("width", 0),
                                                  solar_detection_doc.get("image", {}).get("height", 0),
                                                  filename)

            if not check_if_processed(solar_detection_doc):
                process_solar_detection(postgresql, image_id, solar_detection_doc)
                append_processed_to_document(collection, solar_detection_doc)

            if not check_if_processed(roof_type_doc):
                process_roof_type_prediction(postgresql, image_id, roof_type_doc)
                append_processed_to_document(collection, roof_type_doc)

        postgresql.close()
        logger.info("PostgreSQL connection closed.")


if __name__ == "__main__":
    main()
