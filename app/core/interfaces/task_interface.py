from typing import Protocol, Optional, List
from uuid import UUID

from app.core import entities
from app.presentation import schemas


class TaskInterface(Protocol):
    def create_inference_task(self, task: schemas.TaskCreate) -> entities.Task:
        ...

    def create_training_task(self, task: schemas.TaskCreate) -> entities.Task:
        ...

    def get_task_by_id(self, task_id: UUID) -> Optional[entities.Task]:
        ...

    def get_tasks(self, skip: int = 0, limit: int = 100,
        user_id: Optional[UUID] = None,
        model_id: Optional[UUID] = None
    ) -> list[entities.Task]:
        ...

    def get_tasks_by_user_id(self, user_id: UUID) -> Optional[list[entities.Task]]:
        ...

    def delete_task_by_id(self, task_id: UUID):
        ...
