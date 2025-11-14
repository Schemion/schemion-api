from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.core import entities
from app.presentation import schemas


class DatasetInterface(ABC):
    @abstractmethod
    def create_dataset(self, dataset: schemas.DatasetCreate) -> entities.Dataset:
        ...

    @abstractmethod
    def get_dataset_by_id(self, dataset_id: UUID) -> Optional[entities.Dataset]:
        ...

    @abstractmethod
    def get_datasets(self, skip: int = 0, limit: int = 100, name_contains: Optional[str] = None) -> list[entities.Dataset]:
        ...

    @abstractmethod
    def delete_dataset_by_id(self, dataset_id: UUID):
        ...
