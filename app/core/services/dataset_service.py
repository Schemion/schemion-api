from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import entities
from app.core.enums import CacheKeysList, CacheTTL, CacheKeysObject
from app.core.interfaces import IStorageRepository, IDatasetRepository, ICacheRepository
from app.infrastructure.mappers import EntityJsonMapper
from app.presentation.schemas import DatasetCreate, DatasetRead


class DatasetService:
    def __init__(self, dataset_repo: IDatasetRepository, storage: IStorageRepository, cache_repo: ICacheRepository):
        self.dataset_repo = dataset_repo
        self.storage = storage
        self.cache_repo = cache_repo

    async def create_dataset(self, session: AsyncSession ,dataset: DatasetCreate, file_data: bytes, filename: str, content_type: str, current_user: entities.User) -> entities.Dataset:
        filepath = f"{str(current_user.id)}/{filename}"

        dataset_object = await self.storage.upload_file(file_data, filepath, content_type,
                                                settings.MINIO_DATASETS_BUCKET)
        dataset.minio_path = dataset_object

        created_dataset = await self.dataset_repo.create_dataset(session,dataset, current_user.id)
        await self.cache_repo.delete(CacheKeysObject.dataset(dataset_id=created_dataset.id))
        await self.cache_repo.delete(CacheKeysList.datasets(user_id=current_user.id))
        return created_dataset

    async def get_dataset_by_id(self, session: AsyncSession, dataset_id: UUID, current_user: entities.User) -> Optional[entities.Dataset]:
        cache_key = CacheKeysObject.dataset(dataset_id=dataset_id)
        cached_dataset = await self.cache_repo.get(cache_key)
        if cached_dataset:
            return EntityJsonMapper.from_json(cached_dataset, entities.Dataset)

        dataset = await self._ensure_dataset_exists(session, dataset_id, current_user.id)
        dataset_schema = EntityJsonMapper.to_json(dataset, DatasetRead)
        await self.cache_repo.set(cache_key, dataset_schema, expire=CacheTTL.DATASETS.value)
        return dataset

    async def get_datasets(
            self,
            session: AsyncSession,
            current_user: entities.User,
            skip: int = 0,
            limit: int = 100,
            name_contains: Optional[str] = None,
    ) -> list[entities.Dataset]:
        cache_key = CacheKeysList.datasets(user_id=current_user.id)
        cached_datasets = await self.cache_repo.get(cache_key)
        if cached_datasets:
            return EntityJsonMapper.from_json(cached_datasets, entities.Dataset, as_list=True)

        datasets = await self.dataset_repo.get_datasets(db = session, user_id=current_user.id, skip=skip, limit=limit, name_contains=name_contains)
        datasets_schema = EntityJsonMapper.to_json(datasets, DatasetRead)
        await self.cache_repo.set(cache_key, datasets_schema, expire=CacheTTL.DATASETS.value)
        return datasets

    async def delete_dataset_by_id(self, session: AsyncSession, dataset_id: UUID, current_user: entities.User) -> None:
        dataset = await self._ensure_dataset_exists(session, dataset_id, current_user.id)

        await self.storage.delete_file(dataset.minio_path, settings.MINIO_DATASETS_BUCKET)
        await self.dataset_repo.delete_dataset_by_id(session, dataset_id)
        cache_key = CacheKeysObject.dataset(dataset_id=dataset_id)
        await self.cache_repo.delete(cache_key)

    async def _ensure_dataset_exists(self, session: AsyncSession ,dataset_id: UUID, user_id: UUID):
        dataset = await self.dataset_repo.get_dataset_by_id(session, dataset_id, user_id)
        if not dataset:
            raise HTTPException(status_code=400, detail=f"Dataset with id={dataset_id} does not exist or access denied")

        return dataset