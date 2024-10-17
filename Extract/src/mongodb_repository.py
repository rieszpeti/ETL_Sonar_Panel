import json
from pymongo import MongoClient
import gridfs
import logging
from dataclasses import dataclass, field


@dataclass
class MongoDBConfig:
    connection_string: str = field(metadata={'required': True})
    db_name: str = field(metadata={'required': True})
    username: str = field(metadata={'required': True})
    password: str = field(metadata={'required': True})

    def __post_init__(self):
        if not self.connection_string:
            raise ValueError("The connection string must not be empty.")
        if not self.db_name:
            raise ValueError("The database name must not be empty.")
        if not self.username:
            raise ValueError("The username must not be empty.")
        if not self.password:
            raise ValueError("The password must not be empty.")


class MongoDBRepository:
    def __init__(self, config: MongoDBConfig):
        self.config = config
        self.client = self.connect_to_mongodb()
        self.db = self.client[self.config.db_name]
        self.fs = gridfs.GridFS(self.db)

    def connect_to_mongodb(self):
        try:
            client = MongoClient(self.config.connection_string)
            client.server_info()
            logging.info("Connected to MongoDB successfully.")
            return client
        except Exception as e:
            logging.error("Error connecting to MongoDB: %s", e)
            return None

    def upload_document(self, json_data, filename):
        try:
            # Convert JSON data to bytes
            json_bytes = json.dumps(json_data).encode('utf-8')

            # Upload JSON bytes to GridFS
            self.fs.put(json_bytes, filename=filename)
            logging.info(f"Uploaded {filename} to MongoDB.")
        except Exception as e:
            logging.error("Error uploading JSON to MongoDB: %s", e)

    def is_file_exists(self, filename):
        try:
            file = self.db.fs.files.find_one({"filename": filename})
            if file:
                logging.info(f"File {filename} already exists in MongoDB.")
                return True
            else:
                logging.info(f"File {filename} does not exist in MongoDB.")
                return False
        except Exception as e:
            logging.error(f"Error checking for file {filename} in MongoDB: {e}")
            raise
