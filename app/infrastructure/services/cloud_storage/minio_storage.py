from datetime import timedelta

from miniopy_async import Minio
from app.core.interfaces.storage_interface import IStorageRepository
import uuid
import io

class MinioStorage(IStorageRepository):
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str | None = None, secure: bool = False):
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        self.endpoint = endpoint
        self.public_endpoint = "files.localhost"
        self.bucket = bucket

    async def _ensure_bucket_exists(self, bucket: str) -> None:
        found = await self.client.bucket_exists(bucket)
        if not found:
            await self.client.make_bucket(bucket)

    async def upload_file(self, file_data: bytes, filename: str, content_type: str, bucket: str) -> str:
        await self._ensure_bucket_exists(bucket)
        object_name = f"{uuid.uuid4()}_{filename}"
        await self.client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=io.BytesIO(file_data),
            length=len(file_data),
            content_type=content_type,
        )
        return object_name

    async def delete_file(self, object_name: str, bucket: str) -> None:
        await self.client.remove_object(bucket, object_name)

    #TODO: Работать не будет, так как бакет не публичный
    def get_file_url(self, object_name: str, bucket: str) -> str:
        return f"http://{self.public_endpoint}/{bucket}/{object_name}"

    async def get_presigned_url(self, object_name: str, bucket: str, expires: int = 3600) -> str:
        return await self.client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_name,
            expires=timedelta(seconds=expires)
        )

