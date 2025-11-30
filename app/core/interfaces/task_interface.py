from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import entities
from app.presentation import schemas


class ITaskRepository(ABC):
    @abstractmethod
    async def create_inference_task(self, db: AsyncSession, task: schemas.TaskCreate) -> entities.Task:
        ...

    @abstractmethod
    async def create_training_task(self, db: AsyncSession, task: schemas.TaskCreate) -> entities.Task:
        ...

    @abstractmethod
    async def get_task_by_id(self, db: AsyncSession, task_id: UUID) -> Optional[entities.Task]:
        ...

    @abstractmethod
    async def get_tasks(self, db: AsyncSession, skip: int = 0, limit: int = 100,
        user_id: Optional[UUID] = None,
        model_id: Optional[UUID] = None
    ) -> list[entities.Task]:
        ...

    @abstractmethod
    async def get_tasks_by_user_id(self, db: AsyncSession, user_id: UUID) -> Optional[list[entities.Task]]:
        ...

    @abstractmethod
    async def delete_task_by_id(self, db: AsyncSession, task_id: UUID):
        ...
