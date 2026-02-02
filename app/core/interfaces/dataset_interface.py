from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.infrastructure.database.models import Dataset
from app.presentation import schemas


class IDatasetRepository(ABC):
    @abstractmethod
    async def create_dataset(self, dataset: schemas.DatasetCreate, user_id: UUID) -> Dataset:
        ...

    @abstractmethod
    async def get_dataset_by_id(self, dataset_id: UUID, user_id: Optional[UUID] = None) -> Optional[Dataset]:
        ...

    @abstractmethod
    async def get_datasets(self, user_id: UUID,skip: int = 0, limit: int = 100, name_contains: Optional[str] = None) -> list[Dataset]:
        ...

    @abstractmethod
    async def delete_dataset_by_id(self, dataset_id: UUID):
        ...
