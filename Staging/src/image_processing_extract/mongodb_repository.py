from pymongo import MongoClient
import logging

from mongodb_config import MongoDBConfig


class MongoDBRepository:
    def __init__(self, config: MongoDBConfig):
        client = self.connect_to_mongodb(config.connection_string)
        db = client[config.db_name]
        self.collection = db[config.collection_name]

    def connect_to_mongodb(self, connection_string):
        try:
            client = MongoClient(connection_string)
            client.server_info()
            logging.info("Connected to MongoDB successfully.")
            return client
        except Exception as e:
            logging.error("Error connecting to MongoDB: %s", e)
            return None

    def upload_document(self, json_data, filename, prediction_type):
        try:
            json_data['filename'] = filename
            json_data['prediction_type'] = prediction_type
            self.collection.insert_one(json_data)
            logging.info(f"Uploaded {filename} to MongoDB.")
        except Exception as e:
            logging.error("Error uploading JSON to MongoDB: %s", e)

    def is_file_exists(self, filename):
        try:
            file = self.collection.find_one({"filename": filename})
            if file:
                logging.info(f"File {filename} already exists in MongoDB.")
                return True
            else:
                logging.info(f"File {filename} does not exist in MongoDB.")
                return False
        except Exception as e:
            logging.error(f"Error checking for file {filename} in MongoDB: {e}")
            raise
