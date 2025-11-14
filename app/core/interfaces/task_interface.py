from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.core import entities
from app.presentation import schemas


class TaskInterface(ABC):
    @abstractmethod
    def create_task(self, task: schemas.TaskCreate) -> entities.Task:
        ...

    @abstractmethod
    def get_task_by_id(self, task_id: UUID) -> Optional[entities.Task]:
        ...

    @abstractmethod
    def get_tasks(self, skip: int = 0, limit: int = 100,
        user_id: Optional[UUID] = None,
        model_id: Optional[UUID] = None
    ) -> list[entities.Task]:
        ...

    @abstractmethod
    def get_tasks_by_user_id(self, user_id: UUID) -> Optional[list[entities.Task]]:
        ...

    @abstractmethod
    def delete_task_by_id(self, task_id: UUID):
        ...
