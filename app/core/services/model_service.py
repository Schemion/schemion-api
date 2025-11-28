from typing import Optional
from uuid import UUID

from fastapi import HTTPException

from app.config import settings
from app.core import entities
from app.core.enums import ModelStatus, CacheKeysObject, CacheKeysList, CacheTTL
from app.core.interfaces import IModelRepository, IStorageRepository, IDatasetRepository, ICacheRepository
from app.presentation.schemas import ModelCreate, ModelRead
from app.infrastructure.mappers import EntityJsonMapper


class ModelService:
    def __init__(self, model_repo: IModelRepository, storage: IStorageRepository, dataset_repo: IDatasetRepository, cache_repo: ICacheRepository):
        self.model_repo = model_repo
        self.dataset_repo = dataset_repo
        self.storage = storage
        self.cache_repo = cache_repo

    async def create_model(self,  model: ModelCreate, file_data: bytes, filename: str, content_type: str, current_user: entities.User) -> entities.Model:
        if not file_data:
            raise HTTPException(400, "Uploaded model file is empty")

        if model.dataset_id:
            await self._ensure_dataset_exists(model.dataset_id, current_user.id)

        file_path = f"{str(current_user.id)}/{filename}"

        model_object = await self.storage.upload_file(file_data, file_path, content_type,
                                                settings.MINIO_MODELS_BUCKET)

        model.minio_model_path = model_object
        created_model = await self.model_repo.create_model(model, current_user.id, is_system=False)
        await self.cache_repo.delete(CacheKeysObject.model(model_id=created_model.id))
        await self.cache_repo.delete(CacheKeysList.models(user_id=current_user.id))
        return created_model

    async def get_model_by_id(self, model_id: UUID, current_user: entities.User) -> Optional[entities.Model]:
        cache_key = CacheKeysObject.model(model_id=model_id)
        cached_model = await self.cache_repo.get(cache_key)
        if cached_model:
            return EntityJsonMapper.from_json(cached_model, entities.Model)
        model = await self.model_repo.get_model_by_id(model_id, current_user.id)
        model_schema = EntityJsonMapper.to_json(model, ModelRead)
        await self.cache_repo.set(cache_key, model_schema, expire=CacheTTL.MODELS.value)
        return model

    async def get_models(self, current_user: entities.User, skip: int = 0, limit: int = 100, status: Optional[ModelStatus] = None, dataset_id: Optional[UUID] = None, include_system: bool = True) -> list[entities.Model]:
        cache_key = CacheKeysList.models(user_id=current_user.id)
        cached_models = await self.cache_repo.get(cache_key)
        if cached_models:
            return EntityJsonMapper.from_json(cached_models, entities.Model, as_list=True)

        models = await self.model_repo.get_models(user_id=current_user.id, skip=skip, limit=limit, status=status, dataset_id=dataset_id, include_system=include_system)
        models_schema = EntityJsonMapper.to_json(models, ModelRead)
        await self.cache_repo.set(cache_key, models_schema, expire=CacheTTL.MODELS.value)
        return models

    # TODO: тоже можно добавить кеширование, но потом
    async def get_models_by_dataset_id(self, dataset_id: UUID, current_user: entities.User) -> list[entities.Model]:
        await self._ensure_dataset_exists(dataset_id, current_user.id)

        return await self.model_repo.get_models_by_dataset_id(dataset_id=dataset_id, user_id=current_user.id)

    async def delete_model_by_id(self, model_id: UUID, current_user: entities.User) -> None:
        model = await self._ensure_model_exists(model_id, current_user.id)

        if model.is_system:
            raise HTTPException(403, "Cannot delete system model")

        await self.storage.delete_file(model.minio_model_path, settings.MINIO_MODELS_BUCKET)
        await self.model_repo.delete_model_by_id(model_id, current_user.id)
        cache_key = CacheKeysObject.model(model_id=model_id)
        await self.cache_repo.delete(cache_key)

    async def _ensure_dataset_exists(self, dataset_id: UUID, user_id: UUID):
        dataset = await self.dataset_repo.get_dataset_by_id(dataset_id, user_id)
        if not dataset:
            raise HTTPException(status_code=400, detail=f"Dataset with id={dataset_id} does not exist or access denied")

    async def _ensure_model_exists(self, model_id: UUID, user_id: UUID):
        model = await self.model_repo.get_model_by_id(model_id, user_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model with id={model_id} not found or access denied")
        return model