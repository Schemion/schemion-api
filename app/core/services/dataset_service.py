from typing import Optional
from uuid import UUID

from fastapi import HTTPException

from app.config import settings
from app.core import entities
from app.core.interfaces import IStorageRepository, IDatasetRepository
from app.presentation.schemas import DatasetCreate


class DatasetService:
    def __init__(self, dataset_repo: IDatasetRepository, storage: IStorageRepository):
        self.dataset_repo = dataset_repo
        self.storage = storage

    def create_dataset(self, dataset: DatasetCreate, file_data: bytes, filename: str, content_type: str, current_user: entities.User) -> entities.Dataset:
        dataset_object = self.storage.upload_file(file_data, filename, content_type,
                                                settings.MINIO_DATASETS_BUCKET)
        dataset.minio_path = dataset_object
        return self.dataset_repo.create_dataset(dataset, current_user.id)

    def get_dataset_by_id(self, dataset_id: UUID, current_user: entities.User) -> Optional[entities.Dataset]:
        dataset = self._ensure_dataset_exists(dataset_id, current_user.id)
        return dataset

    def get_datasets(
            self,
            current_user: entities.User,
            skip: int = 0,
            limit: int = 100,
            name_contains: Optional[str] = None,
    ) -> list[entities.Dataset]:
        return self.dataset_repo.get_datasets(user_id=current_user.id, skip=skip, limit=limit, name_contains=name_contains)

    def delete_dataset_by_id(self, dataset_id: UUID, current_user: entities.User) -> None:
        dataset = self._ensure_dataset_exists(dataset_id, current_user.id)

        self.storage.delete_file(dataset.minio_path, settings.MINIO_DATASETS_BUCKET)
        self.dataset_repo.delete_dataset_by_id(dataset_id)

    def _ensure_dataset_exists(self, dataset_id: UUID, user_id: UUID):
        dataset = self.dataset_repo.get_dataset_by_id(dataset_id, user_id)
        if not dataset:
            raise HTTPException(status_code=400, detail=f"Dataset with id={dataset_id} does not exist or access denied")

        return dataset