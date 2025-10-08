from typing import Optional
from uuid import UUID

from app.config import settings
from app.core import entities
from app.core.interfaces import StorageInterface, DatasetInterface
from app.presentation.schemas import DatasetCreate


class DatasetService:
    def __init__(self, dataset_repo: DatasetInterface, storage: StorageInterface):
        self.dataset_repo = dataset_repo
        self.storage = storage

    def create_model(self, dataset: DatasetCreate, file_data: bytes, filename: str, content_type: str) -> entities.Dataset:
        dataset_object = self.storage.upload_file(file_data, filename, content_type,
                                                settings.MINIO_DATASET_BUCKET)
        dataset.input_path = dataset_object
        return self.dataset_repo.create_dataset(dataset)

    def get_dataset_by_id(self, dataset_id: UUID) -> Optional[entities.Dataset]:
        return self.dataset_repo.get_dataset_by_id(dataset_id)

    def get_datasets(
            self,
            skip: int = 0,
            limit: int = 100,
            name_contains: Optional[str] = None,
    ) -> list[entities.Dataset]:
        return self.dataset_repo.get_datasets(skip, limit, name_contains)

    def delete_dataset_by_id(self, dataset_id: UUID) -> None:
        self.dataset_repo.delete_dataset_by_id(dataset_id)