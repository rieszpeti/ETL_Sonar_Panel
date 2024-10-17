import os
from dataclasses import dataclass, field

import cv2
import logging
from roboflow import Roboflow
import supervision as sv
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


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

    def predict_and_annotate(self, image_path, confidence=40):
        try:
            result = self.model.predict(image_path, confidence=confidence).json()
            labels = [item["class"] for item in result["predictions"]]

            detections = sv.Detections.from_inference(result)

            logging.info(f"Total detections: {len(detections)}")

            # Filter by class
            detections = detections[detections.class_id == 0]
            logging.info(f"Filtered detections: {len(detections)}")

            label_annotator = sv.LabelAnnotator()
            mask_annotator = sv.MaskAnnotator()

            image = cv2.imread(image_path)

            annotated_image = mask_annotator.annotate(scene=image, detections=detections)
            annotated_image = label_annotator.annotate(scene=annotated_image, detections=detections, labels=labels)

            return annotated_image
        except Exception as e:
            logging.error("Error predicting and annotating image %s: %s", image_path, e)
            return None

    def process_images_from_folder(self, folder_path):
        for filename in os.listdir(folder_path):
            if filename.endswith(".jpg"):
                image_path = os.path.join(folder_path, filename)
                logging.info(f"Processing {filename}")

                annotated_image = self.predict_and_annotate(image_path)

                if annotated_image is not None:
                    #upload image to db
                    logging.info(f"Annotated image saved: annotated_{filename}")
                else:
                    logging.warning(f"Failed to annotate image: {filename}")


def main():
    api_key = os.getenv("ROBOFLOW_API_KEY")

    project_name = "roof-segmentation-qmhbb"
    version_number = 7
    input_folder = "../resources/roof_from_streetview/pictures"

    params = RoboflowModelParams(api_key, project_name, version_number)

    satellite_image_model = RoboflowModel(params)
    satellite_image_model.process_images_from_folder(input_folder)

    # mekkora a lefedettseg?
    project_name = "solar-panels-81zxz/1"

    streetview_image_model = RoboflowModel(RoboflowModelParams(api_key, project_name, version_number))
    streetview_image_model.process_images_from_folder(input_folder)


if __name__ == "__main__":
    main()
