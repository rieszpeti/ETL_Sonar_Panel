import boto3
import logging
from botocore.exceptions import NoCredentialsError, ClientError
from dataclasses import dataclass


@dataclass
class S3Config:
    endpoint_url: str
    region_name: str = 'us-east-1'
    aws_access_key_id: str = 'test'
    aws_secret_access_key: str = 'test'


class S3Repository:
    def __init__(self, config: S3Config):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=config.endpoint_url,
            region_name=config.region_name,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key
        )

    def create_bucket(self, bucket_name):
        try:
            self.s3_client.create_bucket(Bucket=bucket_name)
            logging.info(f"Bucket {bucket_name} created successfully.")
        except ClientError as e:
            logging.error(f"Error creating bucket {bucket_name}: {e}")
            raise

    def upload_file(self, file_path, bucket_name, object_name):
        try:
            self.s3_client.upload_file(file_path, bucket_name, object_name)
            logging.info(f"File {object_name} uploaded to {bucket_name}.")
        except NoCredentialsError:
            logging.error("Credentials not available")
        except ClientError as e:
            logging.error(f"Error uploading file to {bucket_name}: {e}")

    def download_file(self, bucket_name, object_name, file_path):
        try:
            self.s3_client.download_file(bucket_name, object_name, file_path)
            logging.info(f"File {object_name} downloaded from {bucket_name}.")
        except ClientError as e:
            logging.error(f"Error downloading file from {bucket_name}: {e}")

