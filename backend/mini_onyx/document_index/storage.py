from typing import Protocol

import boto3
from botocore.exceptions import ClientError

from mini_onyx.config import StorageSettings


class FileStore(Protocol):
    def put(self, *, key: str, content: bytes) -> None: ...

    def delete(self, *, key: str) -> None: ...


class S3FileStore:
    def __init__(self, settings: StorageSettings) -> None:
        self._bucket = settings.bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.endpoint,
            aws_access_key_id=settings.access_key,
            aws_secret_access_key=settings.secret_key,
            region_name="us-east-1",
        )

    def put(self, *, key: str, content: bytes) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as error:
            if error.response["Error"]["Code"] not in {"404", "NoSuchBucket"}:
                raise
            self._client.create_bucket(Bucket=self._bucket)

        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=content,
            ContentType="text/plain; charset=utf-8",
        )

    def delete(self, *, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)
