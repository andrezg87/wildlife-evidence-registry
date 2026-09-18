from typing import BinaryIO

import boto3

from app.config import settings

_s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)


def upload_file(key: str, file_obj: BinaryIO) -> str:
    _s3_client.upload_fileobj(file_obj, settings.aws_s3_bucket, key)
    return f"https://{settings.aws_s3_bucket}.s3.{settings.aws_region}.amazonaws.com/{key}"
