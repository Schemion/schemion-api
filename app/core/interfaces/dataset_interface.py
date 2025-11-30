from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import entities
from app.presentation import schemas


class IDatasetRepository(ABC):
    @abstractmethod
    async def create_dataset(self, db: AsyncSession, dataset: schemas.DatasetCreate, user_id: UUID) -> entities.Dataset:
        ...

    @abstractmethod
    async def get_dataset_by_id(self, db: AsyncSession, dataset_id: UUID, user_id: Optional[UUID] = None) -> Optional[entities.Dataset]:
        ...

    @abstractmethod
    async def get_datasets(self, db: AsyncSession, user_id: UUID,skip: int = 0, limit: int = 100, name_contains: Optional[str] = None) -> list[entities.Dataset]:
        ...

    @abstractmethod
    async def delete_dataset_by_id(self, db: AsyncSession, dataset_id: UUID):
        ...
