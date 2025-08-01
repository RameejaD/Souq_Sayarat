import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def get_s3_client():
    return boto3.client(
        's3',
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
