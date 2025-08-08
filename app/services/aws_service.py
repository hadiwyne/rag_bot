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
            
    async def _setup_lambda_function(self):
        try:
            lambda_code = """
import json
import base64

def lambda_handler(event, context):
    try:
    document_id = event.get('document_id')
    content = event.get('content')

    preprocessed_content = content.upper() if content else ""

    return{
    'statusCode': 200,
    'body': json.dumps({
        'document_id': document_id,
        'processed': True,
        'content_length': len(preprocessed_content)
    })
    }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
"""

            self.lambda_client.create_function(
                FunctionName='document-processor',
                Runtime='python3.9',
                Role='arn:aws:iam::000000000000:role/lambda-role',
                Handler='index.lambda_handler',
                Code={'ZipFile': lambda_code.encode()},
                Description='Document processing function'
            )
            print("Created Lambda function 'document-processor' successfully.")

        except Exception as e:
            if "ResourceConflictException" not in str(e):
                raise e
            
    async def store_document(self, document_id: str, content: str, metadata: dict = None) -> bool:
        try:
            document_data = {
                'content': content,
                'metadata': metadata or {}
            }

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=f"documents/{document_id}.json",
                Body=json.dumps(document_data),
                ContentType='application/json'
            )

            return True
        except Exception as e:
            print(f"Error storing document: {str(e)}")
            return False
        
    async def retrieve_document(self, document_id: str) -> Optional[Dict]:
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=f"documents/{document_id}.json"
            )

            document_data = json.loads(response['Body'].read())
            return document_data
        
        except Exception as e:
            print(f"Error retrieving document: {str(e)}")
            return None
        
    async def process_document_async(self, document_id: str, content: str) -> dict:
        try:
            response = self.lambda_client.invoke(
                FunctionName='document-processor',
                Payload=json.dumps({
                    'document_id': document_id,
                    'content': content
                })
            )
            result = json.loads(response['Payload'].read())
            return result
        
        except Exception as e:
            print(f"Error processing document asynchronously: {str(e)}")
            return {'error': str(e)}
        
    async def list_documents(self) -> List[str]:
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='documents/'
            )

            documents = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    doc_id = obj['Key'].replace('documents/', '').replace('.json', '')
                    documents.append(doc_id)

            return documents
        
        except Exception as e:
            print(f"Error listing documents: {str(e)}")
            return []
        
    async def get_service_health(self) -> dict:
        health_status = {
            's3': False,
            'lambda': False,
        }

        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            health_status['s3'] = True
        except:
            pass

        try:
            self.lambda_client.list_functions()
            health_status['lambda'] = True
        except:
            pass

        return health_status