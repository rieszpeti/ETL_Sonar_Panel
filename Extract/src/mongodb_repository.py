from pymongo import MongoClient
import gridfs
import logging
from dataclasses import dataclass, field


@dataclass
class MongoDBConfig:
    connection_string: str = field(metadata={'required': True})
    db_name: str = field(metadata={'required': True})

    def __post_init__(self):
        if not self.connection_string:
            raise ValueError("The connection string must not be empty.")
        if not self.db_name:
            raise ValueError("The database name must not be empty.")


class MongoDBRepository:
    def __init__(self, config: MongoDBConfig):
        self.config = config
        self.client = self.connect_to_mongodb()
        self.db = self.client[self.config.db_name]
        self.fs = gridfs.GridFS(self.db)

    def connect_to_mongodb(self):
        try:
            client = MongoClient(self.config.connection_string)
            logging.info("Connected to MongoDB successfully.")
            return client
        except Exception as e:
            logging.error("Error connecting to MongoDB: %s", e)
            return None

    def upload_image(self, image_path, filename):
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                self.fs.put(image_data, filename=filename)
                logging.info(f"Uploaded {filename} to MongoDB.")
        except Exception as e:
            logging.error("Error uploading image to MongoDB: %s", e)
