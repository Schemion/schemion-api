from typing import Protocol, Optional, List
from uuid import UUID

from app.core import entities
from app.core.enums import ModelStatus
from app.presentation import schemas


class ModelInterface(Protocol):
    def create_model(self, model: schemas.ModelCreate) -> entities.Model:
        ...

    def get_model_by_id(self, model_id: UUID) -> Optional[entities.Model]:
        ...

    def get_models(self, skip: int = 0, limit: int = 100,
        status: Optional[ModelStatus] = None,
        dataset_id: Optional[UUID] = None
    ) -> list[entities.Model]:
        ...

    def get_models_by_dataset_id(self, dataset_id: UUID) -> Optional[list[entities.Model]]:
        ...

    def delete_model_by_id(self, model_id: UUID):
        ...
