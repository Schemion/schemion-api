from typing import Optional
from uuid import UUID

from fastapi import HTTPException

from app.core.enums import CacheKeysList, CacheKeysObject, CacheTTL
from app.core.interfaces import ICacheRepository, IDatasetRepository, IStorageRepository
from app.core.validation import validate_dataset_archive
from app.infrastructure.config import settings
from app.presentation.schemas import DatasetCreate, DatasetRead


class DatasetService:
    def __init__(self, dataset_repo: IDatasetRepository, storage: IStorageRepository, cache_repo: ICacheRepository):
        self.dataset_repo = dataset_repo
        self.storage = storage
        self.cache_repo = cache_repo

    async def create_dataset(self, dataset: DatasetCreate, file_data: bytes, filename: str, content_type: str,
                             user_id: UUID) -> DatasetRead:
        validate_dataset_archive(file_data, filename)

        filepath = f"{user_id}/{filename}"

        dataset.minio_path = await self.storage.upload_file(file_data, filepath, content_type,
                                                            settings.MINIO_DATASETS_BUCKET)

        created = await self.dataset_repo.create_dataset(dataset=dataset, user_id=user_id)

        await self.cache_repo.delete(CacheKeysObject.dataset(dataset_id=created.id))
        await self.cache_repo.delete_pattern(f"{CacheKeysList.DATASETS}:{user_id}:*")

        return created

    async def get_dataset_by_id(self, dataset_id: UUID, user_id: UUID) -> Optional[
        DatasetRead]:
        cache_key = CacheKeysObject.dataset(dataset_id=dataset_id)

        cached = await self.cache_repo.get(cache_key)
        if cached:
            return DatasetRead(**cached)

        dataset = await self._ensure_dataset_exists(dataset_id, user_id)
        await self.cache_repo.set(cache_key, DatasetRead.model_validate(dataset).model_dump(),
                                  expire=CacheTTL.DATASETS.value)

        return dataset

    async def get_datasets(self, user_id: UUID, skip: int = 0, limit: int = 100, name_contains: Optional[str] = None) -> \
    list[DatasetRead]:
        cache_key = CacheKeysList.datasets(user_id=user_id, skip=skip, limit=limit, name_contains=name_contains)
        cached = await self.cache_repo.get(cache_key)
        if cached:
            return [DatasetRead(**item) for item in cached]

        datasets = await self.dataset_repo.get_datasets(user_id=user_id, skip=skip, limit=limit,
                                                        name_contains=name_contains)

        serialized = [DatasetRead.model_validate(dataset).model_dump() for dataset in datasets]

        await self.cache_repo.set(cache_key, serialized, expire=CacheTTL.DATASETS.value)

        return datasets

    async def delete_dataset_by_id(self, dataset_id: UUID, user_id: UUID) -> None:
        dataset = await self._ensure_dataset_exists(dataset_id, user_id)

        await self.storage.delete_file(dataset.minio_path, settings.MINIO_DATASETS_BUCKET)

        await self.dataset_repo.delete_dataset_by_id(dataset_id)

        await self.cache_repo.delete(CacheKeysObject.dataset(dataset_id=dataset_id))
        await self.cache_repo.delete_pattern(f"{CacheKeysList.DATASETS}:{user_id}:*")

    async def _ensure_dataset_exists(self, dataset_id: UUID, user_id: UUID):
        dataset = await self.dataset_repo.get_dataset_by_id(dataset_id, user_id)
        if not dataset:
            raise HTTPException(status_code=400, detail=f"Dataset with id={dataset_id} does not exist or access denied")

        return dataset
