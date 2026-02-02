from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.infrastructure.persistence.models import Task
from app.presentation import schemas


class ITaskRepository(ABC):
    @abstractmethod
    async def create_inference_task(self, task: schemas.TaskCreate) -> Task:
        ...

    @abstractmethod
    async def create_training_task(self, task: schemas.TaskCreate) -> Task:
        ...

    @abstractmethod
    async def get_task_by_id(self, task_id: UUID) -> Optional[Task]:
        ...

    @abstractmethod
    async def get_tasks(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None,
                        model_id: Optional[UUID] = None) -> list[Task]:
        ...

    @abstractmethod
    async def get_tasks_by_user_id(self, user_id: UUID) -> Optional[list[Task]]:
        ...

    @abstractmethod
    async def delete_task_by_id(self, task_id: UUID):
        ...
