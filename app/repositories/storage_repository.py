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
    return key


def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    return _s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.aws_s3_bucket, "Key": key},
        ExpiresIn=expires_in,
    )
