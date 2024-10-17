import logging
import os

import numpy as np
from PIL import Image

from roboflow_model import RoboflowModelFactory
from mongodb_repository import MongoDBRepository
from s3_repository import S3Repository, S3Config


class DataExtractService:
    def __init__(
            self,
            roboflow_model_factory: RoboflowModelFactory,
            models_config: list,
            mongo_repo: MongoDBRepository,
            s3_repo: S3Repository,
    ):
        self.roboflow_models = {}
        self.roboflow_model = roboflow_model_factory
        self.mongo_repo = mongo_repo
        self.s3_repo = s3_repo

        for config in models_config:
            api_key = config['api_key']
            project_name = config['project_name']
            version_number = config['version_number']
            input_folder = config['input_folder']
            model_name = config['model_name']

            self.roboflow_models[model_name] = roboflow_model_factory.create_model(
                api_key, project_name, version_number, input_folder
            )

    def _upload_annotated_image(self, original_image_name, annotated_image):
        """Upload the annotated image to S3 after saving it as a temporary file."""
        if isinstance(annotated_image, np.ndarray):
            # Convert ndarray to an image
            image = Image.fromarray(annotated_image)

            # Define a temporary file path to save the image
            annotated_image_name = f"annotated_{original_image_name}"

            # Save the image to the file system
            image.save(annotated_image_name)
            logging.info(f"Annotated image saved to {annotated_image_name}.")

            # Upload the saved image to S3
            self.s3_repo.upload_file(annotated_image_name)

            # Optionally, clean up by removing the temporary image file
            if os.path.exists(annotated_image_name):
                os.remove(annotated_image_name)
                logging.info(f"Temporary image file {annotated_image_name} removed after upload.")
        else:
            logging.error("Annotated image is not a valid ndarray.")

    def process_images(self):
        for model_name, roboflow_model in self.roboflow_models.items():
            logging.info(f"Processing images for model: {model_name}")
            result = roboflow_model.process_images_from_folder()

            result_filename = f"{result.project_name}_{result.filename}"

            if result.filename:
                if not self.mongo_repo.is_file_exists(result_filename):
                    self.mongo_repo.upload_document(result.result_json,
                                                    result_filename,
                                                    result.project_name)
                else:
                    logging.info(f"Skipping save to MongoDB. File {result.filename} already exists.")

                if not self.s3_repo.is_file_exists(result.filename):
                    self.s3_repo.upload_file(result.image_path)
                else:
                    logging.info(f"Skipping upload to S3. File {result.filename} already exists.")

                if result.annotated_image is not None:
                    self._upload_annotated_image(result.filename, result.annotated_image)
                else:
                    logging.info(f"Skipping upload to S3. File {result.filename} already exists.")
