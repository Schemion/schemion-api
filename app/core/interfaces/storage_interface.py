from abc import ABC, abstractmethod


class IStorageRepository(ABC):
    @abstractmethod
    async def upload_file(self, file_data: bytes, filename: str, content_type: str, bucket: str) -> str:
        ...

    @abstractmethod
    async def delete_file(self, object_name: str, bucket: str) -> None:
        ...

    @abstractmethod
    async def get_presigned_file_url(self, object_name: str, bucket: str, expires: int = 3600) -> str:
        ...
