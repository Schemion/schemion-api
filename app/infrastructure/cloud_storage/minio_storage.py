import json
from datetime import timedelta

from minio import Minio
from app.core.interfaces.storage_interface import StorageInterface
import uuid
import io

class MinioStorage(StorageInterface):
    def __init__(self, endpoint: str, public_endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False):
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        self.endpoint = endpoint
        self.public_endpoint = "files.localhost"
        self.bucket = bucket

        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)
            self.client.set_bucket_policy(bucket, self._make_public_policy(bucket))

    def upload_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        object_name = f"{uuid.uuid4()}_{filename}"
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=io.BytesIO(file_data),
            length=len(file_data),
            content_type=content_type,
        )
        return object_name

    def delete_file(self, object_name: str) -> None:
        self.client.remove_object(self.bucket, object_name)

    def get_file_url(self, object_name: str) -> str:
        return f"http://{self.public_endpoint}/{self.bucket}/{object_name}"

    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        return self.client.presigned_get_object(
            self.bucket,
            object_name,
            expires=timedelta(seconds=expires)
        )

    @staticmethod
    def _make_public_policy(bucket: str) -> str:
        return json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": ["s3:GetObject"],
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Resource": [f"arn:aws:s3:::{bucket}/*"]
                }
            ]
        })