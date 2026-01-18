import re
import zipfile
from io import BytesIO
from typing import Optional
from uuid import UUID

import magic
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import entities
from app.core.enums import CacheKeysList, CacheTTL, CacheKeysObject
from app.core.interfaces import IStorageRepository, IDatasetRepository, ICacheRepository
from app.infrastructure.mappers import EntityJsonMapper
from app.presentation.schemas import DatasetCreate, DatasetRead


MAX_FILENAME_LENGTH = 255
FILENAME_REGEX = re.compile(r'^[a-zA-Z0-9_\-.\s]+$')
ALLOWED_EXTENSION = '.zip'
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff'}
TEXT_EXTENSIONS = {'csv', 'txt', 'yml', 'yaml'}
ALLOWED_MIME_TYPES = {'application/zip', 'application/x-zip-compressed'}
MAX_DATASET_FILE_SIZE = 5 * 1024 ** 3 # 5 гигабухтов

class DatasetService:
    def __init__(self, dataset_repo: IDatasetRepository, storage: IStorageRepository, cache_repo: ICacheRepository):
        self.dataset_repo = dataset_repo
        self.storage = storage
        self.cache_repo = cache_repo

    async def create_dataset(self, session: AsyncSession ,dataset: DatasetCreate, file_data: bytes, filename: str, content_type: str, current_user: entities.User) -> entities.Dataset:
        await self._validate_dataset(file_data, filename)

        filepath = f"{str(current_user.id)}/{filename}"

        dataset_object = await self.storage.upload_file(file_data, filepath, content_type,
                                                settings.MINIO_DATASETS_BUCKET)
        dataset.minio_path = dataset_object

        created_dataset = await self.dataset_repo.create_dataset(session,dataset, current_user.id)
        await self.cache_repo.delete(CacheKeysObject.dataset(dataset_id=created_dataset.id))
        pattern = f"{CacheKeysList.DATASETS}:{current_user.id}:*"
        await self.cache_repo.delete_pattern(pattern)
        return created_dataset

    async def get_dataset_by_id(self, session: AsyncSession, dataset_id: UUID, current_user: entities.User) -> Optional[entities.Dataset]:
        cache_key = CacheKeysObject.dataset(dataset_id=dataset_id)
        cached_dataset: dict | None = await self.cache_repo.get(cache_key)
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
        cache_key = CacheKeysList.datasets(user_id=current_user.id, skip=skip, limit=limit, name_contains=name_contains)
        cached_datasets : dict | None= await self.cache_repo.get(cache_key)
        if cached_datasets:
            return EntityJsonMapper.from_json_as_list(cached_datasets, entities.Dataset)

        datasets = await self.dataset_repo.get_datasets(db = session, user_id=current_user.id, skip=skip, limit=limit, name_contains=name_contains)
        datasets_schema = EntityJsonMapper.to_json(datasets, DatasetRead)
        await self.cache_repo.set(cache_key, datasets_schema, expire=CacheTTL.DATASETS.value)
        return datasets

    async def delete_dataset_by_id(self, session: AsyncSession, dataset_id: UUID, current_user: entities.User) -> None:
        dataset = await self._ensure_dataset_exists(session, dataset_id, current_user.id)

        await self.storage.delete_file(dataset.minio_path, settings.MINIO_DATASETS_BUCKET)
        await self.dataset_repo.delete_dataset_by_id(session, dataset_id)
        await self.cache_repo.delete(CacheKeysObject.dataset(dataset_id=dataset_id))
        pattern = f"{CacheKeysList.DATASETS}:{current_user.id}:*"
        await self.cache_repo.delete(pattern)

    async def _ensure_dataset_exists(self, session: AsyncSession ,dataset_id: UUID, user_id: UUID):
        dataset = await self.dataset_repo.get_dataset_by_id(session, dataset_id, user_id)
        if not dataset:
            raise HTTPException(status_code=400, detail=f"Dataset with id={dataset_id} does not exist or access denied")

        return dataset

    @staticmethod
    async def _validate_dataset(file_data: bytes, filename: str) -> None:
        if not file_data:
            raise HTTPException(400, "Uploaded dataset file is empty")

        if not filename or not filename.strip():
            raise HTTPException(400, "Filename is empty")

        filename = filename.strip()

        if len(filename) > MAX_FILENAME_LENGTH:
            raise HTTPException(400, "Filename is too long")

        if not FILENAME_REGEX.match(filename):
            raise HTTPException(400, "Filename contains invalid characters")

        if len(file_data) > MAX_DATASET_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"Dataset file is too large. Max allowed size is {MAX_DATASET_FILE_SIZE} GB")

        if not filename.lower().endswith(ALLOWED_EXTENSION):
            raise HTTPException(400, f"Only {ALLOWED_EXTENSION} files are allowed")


        try:
            with zipfile.ZipFile(BytesIO(file_data)) as zf:
                infos = zf.infolist()

                files_checked = 0
                has_image = False
                has_text = False

                for info in infos:
                    if info.is_dir():
                        continue

                    parts = info.filename.split("/")
                    if info.filename.startswith("/") or ".." in parts:
                        raise HTTPException(400, "Invalid file path inside zip")

                    ext = info.filename.rsplit(".", 1)[-1].lower()

                    if ext in IMAGE_EXTENSIONS:
                        has_image = True
                    elif ext in TEXT_EXTENSIONS:
                        has_text = True

                    files_checked += 1
                    if files_checked >= 100:
                        break

                if files_checked == 0:
                    raise HTTPException(400, "Zip file contains no files")

                if not has_image:
                    raise HTTPException(400, "Zip file contains no image files")

                if not has_text:
                    raise HTTPException(400, "Zip file contains no annotation files")

        except zipfile.BadZipFile:
            raise HTTPException(400, "Bad zip file")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, f"Failed to validate zip file: {e}")
