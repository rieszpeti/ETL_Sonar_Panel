import json
import os

import logging
from dotenv import load_dotenv

from extract_image_data_service import ImageProcessService
from roboflow_model import RoboflowModelFactory
from logging_config import setup_logging
from image_repository import ImageRepository, PostgresConfig


def load_config(config_file):
    with open(config_file, 'r') as file:
        config = json.load(file)

    for model in config['models_config']:
        model['api_key'] = os.getenv("ROBOFLOW_API_KEY")

    image_folder_path = config['image_folder_path']

    return config, image_folder_path


def main():
    load_dotenv()
    setup_logging()

    config, image_folder_path = load_config('config.json')
    models_config = config['models_config']

    pg_config = PostgresConfig(
        dbname=os.getenv("PG_DBNAME"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST"),
        port=int(os.getenv("PG_PORT"))
    )

    roboflow_model_factory = RoboflowModelFactory()
    image_repository = ImageRepository(pg_config)

    data_service = ImageProcessService(
        roboflow_model_factory=roboflow_model_factory,
        models_config=models_config,
        repository=image_repository,
        image_folder_path=image_folder_path
    )

    try:
        data_service.process_images()
    except Exception as e:
        logging.error(e)


if __name__ == '__main__':
    main()
