import re
from typing import Optional
from uuid import UUID

import magic
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import entities
from app.core.enums import ModelStatus, CacheKeysObject, CacheKeysList, CacheTTL
from app.core.interfaces import IModelRepository, IStorageRepository, IDatasetRepository, ICacheRepository
from app.presentation.schemas import ModelCreate, ModelRead
from app.infrastructure.mappers import EntityJsonMapper


ALLOWED_EXTENSIONS = {'pt', 'pth'}
MAX_FILENAME_LENGTH = 255
FILENAME_REGEX = re.compile(r'^[a-zA-Z0-9_\-.\s]+$')
ALLOWED_MIME_TYPES = {'application/octet-stream', 'application/x-pickle'}
MAX_MODEL_FILE_SIZE = 1024 ** 3 # 1 гигобухт

class ModelService:
    def __init__(self, model_repo: IModelRepository, storage: IStorageRepository, dataset_repo: IDatasetRepository, cache_repo: ICacheRepository):
        self.model_repo = model_repo
        self.dataset_repo = dataset_repo
        self.storage = storage
        self.cache_repo = cache_repo

    async def create_model(self, session: AsyncSession,  model: ModelCreate, file_data: bytes, filename: str, content_type: str, current_user: entities.User) -> entities.Model:
        await self._validate_model_file(file_data, filename)

        if model.dataset_id:
            await self._ensure_dataset_exists(session, model.dataset_id, current_user.id)

        file_path = f"{str(current_user.id)}/{filename}"

        model_object = await self.storage.upload_file(file_data, file_path, content_type,
                                                settings.MINIO_MODELS_BUCKET)

        model.minio_model_path = model_object
        created_model = await self.model_repo.create_model(session, model, current_user.id, is_system=False)
        pattern = f"{CacheKeysList.MODELS}:{current_user.id}:*"
        await self.cache_repo.delete(CacheKeysObject.model(model_id=created_model.id))
        await self.cache_repo.delete_pattern(pattern)
        return created_model

    async def get_model_by_id(self, session: AsyncSession, model_id: UUID, current_user: entities.User) -> Optional[entities.Model]:
        cache_key = CacheKeysObject.model(model_id=model_id)
        cached_model: dict | None = await self.cache_repo.get(cache_key)
        if cached_model:
            return EntityJsonMapper.from_json(cached_model, entities.Model)
        model = await self.model_repo.get_model_by_id(session, model_id, current_user.id)
        if model:
            model_schema = EntityJsonMapper.to_json(model, ModelRead)
            await self.cache_repo.set(cache_key, model_schema, expire=CacheTTL.MODELS.value)
        return model

    async def get_models(self, session: AsyncSession, current_user: entities.User, skip: int = 0, limit: int = 100, status: Optional[ModelStatus] = None, dataset_id: Optional[UUID] = None, include_system: bool = True) -> list[entities.Model]:
        cache_key = CacheKeysList.models(user_id=current_user.id, skip=skip,limit=limit,status=status.value if status else None, dataset_id=dataset_id)
        cached_models: dict | None = await self.cache_repo.get(cache_key)
        if cached_models:
            return EntityJsonMapper.from_json_as_list(cached_models, entities.Model)

        models = await self.model_repo.get_models(db=session, user_id=current_user.id, skip=skip, limit=limit, status=status, dataset_id=dataset_id, include_system=include_system)
        models_schema = EntityJsonMapper.to_json(models, ModelRead)
        await self.cache_repo.set(cache_key, models_schema, expire=CacheTTL.MODELS.value)
        return models


    async def delete_model_by_id(self, session: AsyncSession, model_id: UUID, current_user: entities.User) -> None:
        model = await self._ensure_model_exists(session, model_id, current_user.id)

        if model.is_system:
            raise HTTPException(403, "Cannot delete system model")

        await self.storage.delete_file(model.minio_model_path, settings.MINIO_MODELS_BUCKET)
        await self.model_repo.delete_model_by_id(session, model_id, current_user.id)
        await self.cache_repo.delete(CacheKeysObject.model(model_id=model_id))
        pattern = f"{CacheKeysList.MODELS}:{current_user.id}:*"
        await self.cache_repo.delete_pattern(pattern)


    async def _ensure_dataset_exists(self, session: AsyncSession, dataset_id: UUID, user_id: UUID):
        dataset = await self.dataset_repo.get_dataset_by_id(session, dataset_id, user_id)
        if not dataset:
            raise HTTPException(status_code=400, detail=f"Dataset with id={dataset_id} does not exist or access denied")

    async def _ensure_model_exists(self, session: AsyncSession, model_id: UUID, user_id: UUID):
        model = await self.model_repo.get_model_by_id(session, model_id, user_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model with id={model_id} not found or access denied")
        return model

    @staticmethod
    async def _validate_model_file(file_data: bytes, filename: str):
        if not file_data:
            raise HTTPException(400, "Uploaded model file is empty")

        if not filename or not filename.strip():
            raise HTTPException(400, "Uploaded file is empty")

        filename = filename.strip()

        if "." not in filename:
            raise HTTPException(400, "Filename must have extension")

        if len(filename) > MAX_FILENAME_LENGTH:
            raise HTTPException(400, "Filename is too long")

        if not FILENAME_REGEX.match(filename):
            raise HTTPException(400, "Filename contains invalid characters")

        ext = filename.rsplit(".", 1)[1]
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(400, "Filename extension is invalid. Only pt & pth allowed")

        if len(file_data) > MAX_MODEL_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Model file size exceeds 1GB limit")

        try:
            mime_type = magic.from_buffer(file_data, mime=True)
        except Exception as e:
            raise HTTPException(400, f"Failed to determine mime type. Error {e}")

        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(400, f"Invalid file type: {mime_type}")