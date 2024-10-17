import os

from dotenv import load_dotenv

from extract_image_data_service import DataExtractService
from mongodb_repository import MongoDBRepository
from roboflow_model import RoboflowModelFactory
from s3_repository import S3Config, S3Repository
from logging_config import setup_logging
from mongodb_config import MongoDBConfig


def main():
    load_dotenv()
    setup_logging()

    models_config = [
        {
            'api_key': os.getenv("ROBOFLOW_API_KEY"),
            'project_name': "roof-type-classifier-bafod",
            'version_number': 1,
            'input_folder': "resources/roof_satellite/pictures",
            'model_name': "satellite_image_model"
        },
        {
            'api_key': os.getenv("ROBOFLOW_API_KEY"),
            'project_name': "solar-panels-81zxz",
            'version_number': 1,
            'input_folder': "resources/roof_satellite/pictures",
            'model_name': "streetview_image_model"
        },
    ]

    mongo_config = MongoDBConfig(
        connection_string=os.getenv('MONGODB_CONNECTION_STRING'),
        db_name=os.getenv('MONGODB_DB_NAME_SATELLITE'),
        collection_name=os.getenv('MONGODB_DB_COLLECTION_SATELLITE')
    )

    s3_config = S3Config(
        endpoint_url=os.getenv('S3_ENDPOINT_URL'),
        bucket_name=os.getenv('S3_BUCKET_NAME'),
        region_name=os.getenv('S3_REGION_NAME'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

    roboflow_model_factory = RoboflowModelFactory()
    mongo_repo = MongoDBRepository(mongo_config)
    s3_repo = S3Repository(s3_config)

    data_service = DataExtractService(
        roboflow_model_factory,
        models_config,
        mongo_repo,
        s3_repo
    )

    data_service.process_images()


if __name__ == '__main__':
    main()
