from typing import Optional
from uuid import UUID

from app.core.enums import CacheKeysList, CacheKeysObject, CacheTTL
from app.core.exceptions import NotFoundError
from app.core.interfaces import ICacheRepository, IDatasetRepository, IModelRepository, IStorageRepository
from app.core.validation import validate_model_file
from app.infrastructure.config import settings
from app.presentation.schemas import ModelCreate, ModelRead


class ModelService:
    def __init__(self, model_repo: IModelRepository, storage: IStorageRepository, dataset_repo: IDatasetRepository,
                 cache_repo: ICacheRepository):
        self.model_repo = model_repo
        self.dataset_repo = dataset_repo
        self.storage = storage
        self.cache_repo = cache_repo

    async def create_model(self, model: ModelCreate, file_data: bytes, filename: str,
                           content_type: str, user_id: UUID) -> ModelRead:
        await validate_model_file(file_data, filename)

        if model.dataset_id:
            await self._ensure_dataset_exists(model.dataset_id, user_id)

        file_path = f"{str(user_id)}/{filename}"

        model_object = await self.storage.upload_file(file_data, file_path, content_type,
                                                      settings.MINIO_MODELS_BUCKET)

        model.minio_model_path = model_object
        created_model = await self.model_repo.create_model(model, user_id, is_system=False)
        pattern = f"{CacheKeysList.MODELS}:{user_id}:*"
        await self.cache_repo.delete(CacheKeysObject.model(model_id=created_model.id))
        await self.cache_repo.delete_pattern(pattern)
        return created_model

    async def get_model_by_id(self, model_id: UUID, user_id: UUID) -> Optional[
        ModelRead]:
        cache_key = CacheKeysObject.model(model_id=model_id)
        cached = await self.cache_repo.get(cache_key)
        if cached:
            return ModelRead(**cached)

        model = await self._ensure_model_exists(model_id, user_id)

        if model.user_id != user_id:
            raise PermissionError("Access denied")

        await self.cache_repo.set(cache_key, ModelRead.model_validate(model).model_dump(), expire=CacheTTL.MODELS.value)

        return model

    async def get_models(self, user_id: UUID, skip: int = 0, limit: int = 100,
                        dataset_id: Optional[UUID] = None,
                         include_system: bool = True) -> list[ModelRead]:
        cache_key = CacheKeysList.models(user_id=user_id, skip=skip, limit=limit, dataset_id=dataset_id)
        cached = await self.cache_repo.get(cache_key)
        if cached:
            return [ModelRead(**item) for item in cached]

        models = await self.model_repo.get_models(user_id=user_id, skip=skip, limit=limit,
                                                  dataset_id=dataset_id, include_system=include_system)
        serialized = [ModelRead.model_validate(model).model_dump() for model in models]

        await self.cache_repo.set(cache_key, serialized, expire=CacheTTL.MODELS.value)
        return models

    async def delete_model_by_id(self, model_id: UUID, user_id: UUID) -> None:
        model = await self._ensure_model_exists(model_id, user_id)

        if model.is_system:
            raise PermissionError("Cannot delete system model")

        if model.user_id != user_id:
            raise PermissionError("Access denied")

        await self.storage.delete_file(model.minio_model_path, settings.MINIO_MODELS_BUCKET)
        await self.model_repo.delete_model_by_id(model_id, user_id)
        await self.cache_repo.delete(CacheKeysObject.model(model_id=model_id))
        await self.cache_repo.delete_pattern(f"{CacheKeysList.TASKS}:{user_id}")

    async def download_model(self, model_id: UUID, user_id: UUID) -> str:
        model = await self._ensure_model_exists(model_id, user_id)
        if model.user_id != user_id:
            raise PermissionError("Access denied")
        if model.is_system:
            raise PermissionError("Cannot download system model")
        return await self.storage.get_presigned_file_url(model.minio_model_path, settings.MINIO_MODELS_BUCKET)

    async def _ensure_dataset_exists(self, dataset_id: UUID, user_id: UUID):
        dataset = await self.dataset_repo.get_dataset_by_id(dataset_id, user_id)
        if not dataset:
            raise NotFoundError(f"Dataset with id {dataset_id} does not exist or access denied")

    async def _ensure_model_exists(self, model_id: UUID, user_id: UUID):
        model = await self.model_repo.get_model_by_id(model_id, user_id)
        if not model:
            raise NotFoundError(f"Model with id {model_id} not found or access denied")
        return model
