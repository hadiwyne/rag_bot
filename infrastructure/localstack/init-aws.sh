#!/bin/bash

echo "Initializing AWS resources in LocalStack..."

# Wait for LocalStack to be ready
sleep 10

# Create S3 bucket
awslocal s3 mb s3://enterprise-documents

# Create IAM role for Lambda
awslocal iam create-role \
  --role-name lambda-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'

echo "AWS resources initialized successfully!"