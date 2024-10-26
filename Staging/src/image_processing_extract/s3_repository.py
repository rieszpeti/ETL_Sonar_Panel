import os

import boto3
import logging
from botocore.exceptions import NoCredentialsError, ClientError
from dataclasses import dataclass, field


@dataclass
class S3Config:
    endpoint_url: str = field(metadata={'required': True})
    region_name: str = field(metadata={'required': True})
    bucket_name: str = field(metadata={'required': True})
    aws_access_key_id: str = field(metadata={'required': True})
    aws_secret_access_key: str = field(metadata={'required': True})

    def __post_init__(self):
        if not self.endpoint_url:
            raise ValueError("The endpoint URL must not be empty.")
        if not self.region_name:
            raise ValueError("The region name must not be empty.")
        if not self.bucket_name:
            raise ValueError("The bucket name URL must not be empty.")
        if not self.aws_access_key_id:
            raise ValueError("AWS Access Key ID must not be empty.")
        if not self.aws_secret_access_key:
            raise ValueError("AWS Secret Access Key must not be empty.")


class S3Repository:
    def __init__(self, config: S3Config):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=config.endpoint_url,
            region_name=config.region_name,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key
        )

        self.bucket_name = config.bucket_name

        self._create_bucket()

    def _bucket_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False

    def _create_bucket(self):
        if not self._bucket_exists():
            try:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={
                        'LocationConstraint': self.s3_client.meta.region_name
                    }
                )
                print(f'Bucket "{self.bucket_name}" created successfully.')
            except ClientError as e:
                print(f'Error creating bucket: {e}')
        else:
            print(f'Bucket "{self.bucket_name}" already exists.')

    def upload_file(self, file_path):
        object_name = os.path.basename(file_path)
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)
            logging.info(f"File {object_name} uploaded to {self.bucket_name}.")
        except NoCredentialsError:
            logging.error("Credentials not available")
        except ClientError as e:
            logging.error(f"Error uploading file to {self.bucket_name}: {e}")

    def is_file_exists(self, object_name):
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=object_name)
            logging.info(f"File {object_name} exists in {self.bucket_name}.")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logging.info(f"File {object_name} does not exist in {self.bucket_name}.")
                return False
            else:
                logging.error(f"Error checking file in {self.bucket_name}: {e}")
                raise
