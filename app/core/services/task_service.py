from typing import Optional
from uuid import UUID

from app.core import entities
from app.core.interfaces import TaskInterface, StorageInterface
from app.config import settings
from app.presentation.schemas import TaskCreate


class TaskService:
    def __init__(self, task_repo: TaskInterface, storage: StorageInterface):
        self.task_repo = task_repo
        self.storage = storage

    def create_inference_task(self, task: TaskCreate, file_data: bytes, filename: str, content_type: str) -> entities.Task:
        input_object = self.storage.upload_file(file_data, filename, content_type, settings.MINIO_SCHEMAS_BUCKET) # Схемы потому что загружают схемы
        task.input_path = input_object
        return self.task_repo.create_inference_task(task)

    def create_training_task(self, task: TaskCreate) -> entities.Task:
        return self.task_repo.create_training_task(task)

    def get_task_by_id(self, task_id: UUID) -> Optional[entities.Task]:
        return self.task_repo.get_task_by_id(task_id)

    def get_tasks(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None, model_id: Optional[UUID] = None) -> list[entities.Task]:
        return self.task_repo.get_tasks(skip, limit, user_id, model_id)

    def get_tasks_by_user_id(self, user_id: UUID) -> Optional[list[entities.Task]]:
        return self.task_repo.get_tasks_by_user_id(user_id)

    def delete_task_by_id(self, task_id: UUID) -> None:
        self.task_repo.delete_task_by_id(task_id)