from typing import Protocol, Optional
from uuid import UUID

from app.core import entities
from app.presentation import schemas


class DatasetInterface(Protocol):
    def create_dataset(self, dataset: schemas.DatasetCreate) -> entities.Dataset:
        ...

    def get_dataset_by_id(self, dataset_id: UUID) -> Optional[entities.Dataset]:
        ...

    def get_datasets(self, skip: int = 0, limit: int = 100, name_contains: Optional[str] = None) -> list[entities.Dataset]:
        ...

    def delete_dataset_by_id(self, dataset_id: UUID):
        ...
