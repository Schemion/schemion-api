from datetime import timezone, datetime
from typing import Optional
from uuid import UUID

from app.core import entities
from app.core.enums import QueueTypes, TaskStatus
from app.core.interfaces import TaskInterface, StorageInterface
from app.config import settings
from app.infrastructure.messaging import RabbitMQPublisher
from app.presentation.schemas import TaskCreate


class TaskService:
    def __init__(self, task_repo: TaskInterface, storage: StorageInterface):
        self.task_repo = task_repo
        self.storage = storage
        self.publisher = RabbitMQPublisher()

    def create_inference_task(self, task: TaskCreate, file_data: bytes, filename: str, content_type: str) -> entities.Task:
        input_object = self.storage.upload_file(file_data, filename, content_type, settings.MINIO_SCHEMAS_BUCKET) # Схемы потому что загружают схемы
        task.input_path = input_object
        created_task = self.task_repo.create_inference_task(task)

        #TODO: добавить сюда не айди модели а подписанную ссылку из minio, а также архитектуру модели
        message = {
            "task_id": str(created_task.id),
            "task_type": TaskStatus.inference,
            "model_id": str(task.model_id),
            "input_path": input_object,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self.publisher.publish(QueueTypes.inference_queue, message)
        return created_task

    def create_training_task(self, task: TaskCreate) -> entities.Task:
        created_task = self.task_repo.create_training_task(task)

        #TODO: добавить сюда архитектуру модели
        message = {
            "task_id": str(created_task.id),
            "task_type": TaskStatus.training,
            "dataset_id": str(task.dataset_id),
            "model_id": str(task.model_id),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self.publisher.publish(QueueTypes.training_queue, message)
        return created_task

    def get_task_by_id(self, task_id: UUID) -> Optional[entities.Task]:
        return self.task_repo.get_task_by_id(task_id)

    def get_tasks(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None, model_id: Optional[UUID] = None) -> list[entities.Task]:
        return self.task_repo.get_tasks(skip, limit, user_id, model_id)

    def get_tasks_by_user_id(self, user_id: UUID) -> Optional[list[entities.Task]]:
        return self.task_repo.get_tasks_by_user_id(user_id)

    def delete_task_by_id(self, task_id: UUID) -> None:
        self.task_repo.delete_task_by_id(task_id)