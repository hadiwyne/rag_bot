import boto3
from botocore.config import Config
from typing import Dict, List, Optional
import json
from app.core.config import settings

class AWSService:
    def __init__(self):
        self.config = Config(
            region_name=settings.aws_default_region,
            retries={'max_attempts': 2}
        )

        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=self.config
        )

        self.lambda_client = boto3.client(
            'lambda',
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=self.config
        )

        self.opensearch_client = boto3.client(
            'opensearch',
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=self.config
        )

        self.bucket_name = "enterprise-documents"

    async def setup_infrastructure(self):
        try:
            await self._create_s3_bucket()
            await self._setup_lambda_function()

            return True
        except Exception as e:
            print(f"Error setting up AWS infrastructure: {str(e)}")
            return False
        
    async def _create_s3_bucket(self):
        try:
            self.s3_client.create_bucket(Bucket=self.bucket_name)
            print(f"S3 bucket '{self.bucket_name}' created successfully.")
        except Exception as e:
            if "BucketAlreadyOwnedByYou" not in str(e):
                raise e