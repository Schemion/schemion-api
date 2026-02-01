from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID


from app.core.enums import ModelStatus
from app.infrastructure.database.models import Model
from app.presentation import schemas


class IModelRepository(ABC):
    @abstractmethod
    async def create_model(self, model: schemas.ModelCreate, user_id: UUID,  is_system: bool) -> Model:
        ...

    @abstractmethod
    async def get_model_by_id(self, model_id: UUID, user_id: Optional[UUID] = None) -> Optional[Model]:
        ...

    @abstractmethod
    async def get_models(self, user_id: UUID, include_system: bool, skip: int = 0, limit: int = 100,
        status: Optional[ModelStatus] = None,
        dataset_id: Optional[UUID] = None
    ) -> list[Model]:
        ...

    @abstractmethod
    async def get_models_by_dataset_id(self, dataset_id: UUID, user_id: UUID) -> Optional[list[Model]]:
        ...

    @abstractmethod
    async def delete_model_by_id(self, model_id: UUID, user_id: UUID) -> None:
        ...
