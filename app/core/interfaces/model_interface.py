from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import entities
from app.core.enums import ModelStatus
from app.presentation import schemas


class IModelRepository(ABC):
    @abstractmethod
    async def create_model(self, db: AsyncSession, model: schemas.ModelCreate, user_id: UUID,  is_system: bool) -> entities.Model:
        ...

    @abstractmethod
    async def get_model_by_id(self, db: AsyncSession, model_id: UUID, user_id: Optional[UUID] = None) -> Optional[entities.Model]:
        ...

    @abstractmethod
    async def get_models(self, db: AsyncSession, user_id: UUID, include_system: bool, skip: int = 0, limit: int = 100,
        status: Optional[ModelStatus] = None,
        dataset_id: Optional[UUID] = None
    ) -> list[entities.Model]:
        ...

    @abstractmethod
    async def get_models_by_dataset_id(self, db: AsyncSession, dataset_id: UUID, user_id: UUID) -> Optional[list[entities.Model]]:
        ...

    @abstractmethod
    async def delete_model_by_id(self, db: AsyncSession, model_id: UUID, user_id: UUID) -> None:
        ...
