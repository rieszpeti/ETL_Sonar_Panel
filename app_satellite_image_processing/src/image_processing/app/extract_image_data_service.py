import logging
import os
from typing import Tuple, Optional

import numpy as np
from PIL import Image
from io import BytesIO
import random

from roboflow_model import RoboflowModelFactory
from image_repository import ImageRepository


class ImageProcessService:
    def __init__(
            self,
            roboflow_model_factory: RoboflowModelFactory,
            models_config: list,
            repository: ImageRepository,
            image_folder_path: str
    ):
        self.roboflow_models = {}
        self.roboflow_model = roboflow_model_factory
        self.repository = repository
        self.image_folder_path = image_folder_path

        for config in models_config:
            api_key = config['api_key']
            project_name = config['project_name']
            version_number = config['version_number']
            model_name = config['model_name']

            self.roboflow_models[model_name] = roboflow_model_factory.create_model(
                api_key, project_name, version_number
            )

    def _get_files_from_folder(self, file_extension=".jpg"):
        try:
            all_files = os.listdir(self.image_folder_path)
            return [f for f in all_files if f.endswith(file_extension)]
        except Exception as e:
            logging.error(f"Error accessing folder: {e}")
            return []

    @staticmethod
    def _generate_random_coordinate_hungary() -> Tuple[float, float]:
        """Generate a single random coordinate within the boundaries of Hungary."""
        latitude = random.uniform(45.87, 48.58)
        longitude = random.uniform(16.16, 22.89)
        return latitude, longitude

    def process_images(self):
        images = self._get_files_from_folder()
        for image_filename in images:
            logging.info(f"Processing image: {image_filename}")
            image_path = os.path.join(self.image_folder_path, image_filename)
            self._process_single_image(image_filename, image_path)

    def _process_single_image(self, image_filename: str, image_path: str):
        existing_image = self.repository.get_image_by_filename(image_filename)
        if existing_image:
            logging.info(f"Image {image_filename} already exists in the database. Skipping insertion.")
            image_id = existing_image[0]
        else:
            image_id = self._insert_image(image_filename, image_path)

        if image_id is not None:
            self._process_with_models(image_path, image_id)

    def _insert_image(self, image_filename: str, image_path: str):
        with Image.open(image_path) as img:
            width, height = img.size
            image_data = self.read_image_file(image_path)

        image_id = self.repository.insert_image(width, height, image_filename, image_data)
        if image_id is None:
            logging.error(f"Failed to insert image {image_filename} into the database.")
            return None

        self._insert_coordinate_if_needed(image_id)
        return image_id

    def _insert_coordinate_if_needed(self, image_id: int):
        existing_coordinate = self.repository.get_first_coordinate_by_image_id(image_id)
        if existing_coordinate is None:
            random_coord = self._generate_random_coordinate_hungary()
            latitude, longitude = random_coord
            self.repository.insert_coordinate(image_id, latitude, longitude)

    def _process_with_models(self, image_path: str, image_id: int):
        for model_name, roboflow_model in self.roboflow_models.items():

            if model_name == "roof-type-classifier-bafod" and not self.repository.has_predictions(image_id):
                continue

            if model_name == "solar-panels-81zxz" and not self.repository.has_detections(image_id):
                continue

            logging.info(f"Processing image with model: {model_name}")
            result = roboflow_model.process_single_image(image_path)

            if result is not None:
                self._handle_model_results(result, image_id)

    def _handle_model_results(self, result, image_id: int):
        result_json = result.result_json

        if result.project_name == "roof-type-classifier-bafod":
            self._process_roof_type_predictions(result_json, image_id)
        elif result.project_name == "solar-panels-81zxz":
            self._process_solar_panel_detections(result_json, result.annotated_image, image_id)

    def _process_roof_type_predictions(self, result_json, image_id: int):
        if "predictions" in result_json and result_json["predictions"]:
            first_prediction = result_json["predictions"][0]
            if "predictions" in first_prediction:
                for class_name, details in first_prediction["predictions"].items():
                    confidence = details.get("confidence")
                    self.repository.insert_prediction_roof_type(
                        image_id=image_id,
                        class_name=class_name,
                        time_taken=first_prediction.get("time"),
                        confidence=confidence,
                        prediction_type="roof-type-classifier-bafod"  # Example, adjust as necessary
                    )

    def _process_solar_panel_detections(self, result_json, annotated_image: np.ndarray, image_id: int):
        if "predictions" in result_json and result_json["predictions"]:
            first_prediction = result_json["predictions"][0]

            if all(key in first_prediction for key in ["class", "confidence", "x", "y", "width", "height"]):
                class_name = first_prediction["class"]
                confidence = first_prediction["confidence"]
                x = first_prediction["x"]
                y = first_prediction["y"]
                width = first_prediction["width"]
                height = first_prediction["height"]

                image_data = self.convert_annotated_image_to_bytes(annotated_image)

                self.repository.insert_detection_solar_panel(
                    image_id=image_id,
                    class_name=class_name,
                    confidence=confidence,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    image_data=image_data
                )
            else:
                self.repository.insert_no_predictions(image_id)

    @staticmethod
    def convert_annotated_image_to_bytes(annotated_image: np.ndarray) -> Optional[bytes]:
        """Convert a NumPy ndarray representing an annotated image to a bytes representation."""
        if annotated_image is not None:
            image = Image.fromarray(annotated_image)
            byte_stream = BytesIO()
            image.save(byte_stream, format='PNG')
            byte_stream.seek(0)
            return byte_stream.read()
        else:
            logging.info("Annotated image is None.")
            return None

    @staticmethod
    def read_image_file(image_path: str) -> bytes:
        """Read an image file and return its bytes."""
        with open(image_path, 'rb') as f:
            return f.read()
