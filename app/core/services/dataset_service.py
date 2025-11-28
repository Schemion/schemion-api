from typing import Optional
from uuid import UUID

from fastapi import HTTPException

from app.config import settings
from app.core import entities
from app.core.enums import CacheKeysList, CacheTTL, CacheKeysObject
from app.core.interfaces import IStorageRepository, IDatasetRepository, ICacheRepository
from app.presentation.schemas import DatasetCreate


class DatasetService:
    def __init__(self, dataset_repo: IDatasetRepository, storage: IStorageRepository, cache_repo: ICacheRepository):
        self.dataset_repo = dataset_repo
        self.storage = storage
        self.cache_repo = cache_repo

    def create_dataset(self, dataset: DatasetCreate, file_data: bytes, filename: str, content_type: str, current_user: entities.User) -> entities.Dataset:
        filepath = f"{str(current_user.id)}/{filename}"

        dataset_object = self.storage.upload_file(file_data, filepath, content_type,
                                                settings.MINIO_DATASETS_BUCKET)
        dataset.minio_path = dataset_object

        created_dataset = self.dataset_repo.create_dataset(dataset, current_user.id)
        cache_key = CacheKeysObject.dataset(dataset_id=created_dataset.id)
        self.cache_repo.delete(cache_key)
        return created_dataset

    def get_dataset_by_id(self, dataset_id: UUID, current_user: entities.User) -> Optional[entities.Dataset]:
        cache_key = CacheKeysObject.dataset(dataset_id=dataset_id)
        cached_dataset = self.cache_repo.get(cache_key)
        if cached_dataset:
            return cached_dataset

        dataset = self._ensure_dataset_exists(dataset_id, current_user.id)
        self.cache_repo.set(cache_key, dataset, expire=CacheTTL.DATASETS)
        return dataset

    def get_datasets(
            self,
            current_user: entities.User,
            skip: int = 0,
            limit: int = 100,
            name_contains: Optional[str] = None,
    ) -> list[entities.Dataset]:
        cache_key = CacheKeysList.datasets(user_id=current_user.id)
        cached_datasets = self.cache_repo.get(cache_key)
        if cached_datasets:
            return cached_datasets

        datasets = self.dataset_repo.get_datasets(user_id=current_user.id, skip=skip, limit=limit, name_contains=name_contains)
        self.cache_repo.set(cache_key, datasets, expire=CacheTTL.DATASETS)
        return datasets

    def delete_dataset_by_id(self, dataset_id: UUID, current_user: entities.User) -> None:
        dataset = self._ensure_dataset_exists(dataset_id, current_user.id)

        self.storage.delete_file(dataset.minio_path, settings.MINIO_DATASETS_BUCKET)
        self.dataset_repo.delete_dataset_by_id(dataset_id)
        cache_key = CacheKeysObject.dataset(dataset_id=dataset_id)
        self.cache_repo.delete(cache_key)

    def _ensure_dataset_exists(self, dataset_id: UUID, user_id: UUID):
        dataset = self.dataset_repo.get_dataset_by_id(dataset_id, user_id)
        if not dataset:
            raise HTTPException(status_code=400, detail=f"Dataset with id={dataset_id} does not exist or access denied")

        return dataset