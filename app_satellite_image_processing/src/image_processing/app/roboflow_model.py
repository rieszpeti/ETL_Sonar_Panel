import os
from dataclasses import dataclass, field
from typing import Optional

import cv2
import logging
from roboflow import Roboflow
import supervision as sv


class ImageProcessingResult:
    def __init__(self, result_json, annotated_image, project_name, filename):
        self.result_json = result_json
        self.annotated_image = annotated_image
        self.project_name = project_name
        self.filename = filename


@dataclass
class RoboflowModelParams:
    api_key: str = field(metadata={'required': True})
    project_name: str = field(metadata={'required': True})
    version_number: int = field(metadata={'required': True})

    def __post_init__(self):
        if self.api_key is None:
            raise ValueError("API key must not be None.")
        if self.project_name is None:
            raise ValueError("Project name must not be None.")
        if self.version_number is None:
            raise ValueError("Version number must not be None.")


class RoboflowModel:
    def __init__(self, params: RoboflowModelParams):
        self.params = params
        self.model = self.initialize_model()

    def initialize_model(self):
        try:
            rf = Roboflow(api_key=self.params.api_key)
            project = rf.workspace().project(self.params.project_name)
            return project.version(self.params.version_number).model
        except Exception as e:
            logging.error("Error initializing model: %s", e)
            return None

    def predict_and_annotate(self, image_path):
        try:
            result_json = self.model.predict(image_path).json()

            # not a nice pattern but it is okay now to keep it simple
            try:
                labels = [item["class"] for item in result_json["predictions"]]

                detections = sv.Detections.from_inference(result_json)

                logging.info(f"Total detections: {len(detections)}")

                # annotate image
                label_annotator = sv.LabelAnnotator()
                mask_annotator = sv.MaskAnnotator()

                image = cv2.imread(image_path)

                annotated_image = mask_annotator.annotate(scene=image, detections=detections)
                annotated_image = label_annotator.annotate(scene=annotated_image, detections=detections, labels=labels)

                return result_json, annotated_image

            except Exception as e:
                logging.info("Error predicting and annotating image %s: %s", image_path, e)

            return result_json, None

        except Exception as e:
            logging.error("Error predicting and annotating image %s: %s", image_path, e)
            return None

    def process_single_image(self, image_path: str) -> Optional[ImageProcessingResult]:
        """Process a single image."""
        logging.info(f"Processing {image_path}")

        if not os.path.isfile(image_path):
            logging.warning(f"File does not exist: {image_path}")
            return None
        
        result_json, annotated_image = self.predict_and_annotate(image_path)

        if result_json is not None:
            filename = os.path.basename(image_path)
            return ImageProcessingResult(
                result_json=result_json,
                annotated_image=annotated_image,
                project_name=self.params.project_name,
                filename=filename
            )
        else:
            logging.warning(f"Failed to annotate image: {image_path}")
            return None


class RoboflowModelFactory:
    @staticmethod
    def create_model(api_key: str, project_name: str, version_number: int) -> RoboflowModel:
        """Creates and returns an instance of RoboflowModel with the provided parameters."""
        params = RoboflowModelParams(api_key, project_name, version_number)
        return RoboflowModel(params)