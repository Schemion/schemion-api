from datetime import timezone, datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException

from app.core import entities
from app.core.enums import QueueTypes, TaskStatus
from app.core.interfaces import ITaskRepository, IStorageRepository, IModelRepository, IDatasetRepository
from app.config import settings
from app.infrastructure.messaging import RabbitMQPublisher
from app.presentation.schemas import TaskCreate


class TaskService:
    def __init__(self, task_repo: ITaskRepository, storage: IStorageRepository, model_repo: IModelRepository, dataset_repo: IDatasetRepository):
        self.task_repo = task_repo
        self.storage = storage
        self.model_repo = model_repo
        self.dataset_repo = dataset_repo
        self.publisher = RabbitMQPublisher()

    def create_inference_task(self, task: TaskCreate, file_data: bytes, filename: str, content_type: str) -> entities.Task:
        self._ensure_model_exists(task.model_id)

        allowed_types = ["image/jpeg", "image/png", "application/pdf"]
        if content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}.")

        input_object_path = self.storage.upload_file(file_data, filename, content_type, settings.MINIO_SCHEMAS_BUCKET)
        task.input_path = input_object_path
        created = self.task_repo.create_inference_task(task)
        model = self.model_repo.get_model_by_id(task.model_id)

        message = {
            "task_id": str(created.id),
            "task_type": TaskStatus.inference,
            "model_id": str(task.model_id),
            "model_arch": model.architecture if hasattr(model, "architecture") else None,
            "input_path": input_object_path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self._publish(QueueTypes.inference_queue, message)
        return created

    def create_training_task(self, task: TaskCreate) -> entities.Task:
        self._ensure_model_exists(task.model_id)

        if task.dataset_id:
            self._ensure_dataset_exists(task.dataset_id)

        created = self.task_repo.create_training_task(task)
        model = self.model_repo.get_model_by_id(task.model_id)

        message = {
            "task_id": str(created.id),
            "task_type": TaskStatus.training,
            "model_id": str(task.model_id),
            "model_arch": model.architecture if hasattr(model, "architecture") else None,
            "dataset_id": str(task.dataset_id) if task.dataset_id else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self._publish(QueueTypes.training_queue, message)
        return created

    def get_task_by_id(self, task_id: UUID) -> Optional[entities.Task]:
        return self.task_repo.get_task_by_id(task_id)

    def get_tasks(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None, model_id: Optional[UUID] = None) -> list[entities.Task]:
        return self.task_repo.get_tasks(skip, limit, user_id, model_id)

    def get_tasks_by_user_id(self, user_id: UUID) -> list[entities.Task]:
        return self.task_repo.get_tasks_by_user_id(user_id)

    def delete_task_by_id(self, task_id: UUID) -> None:
        self.task_repo.delete_task_by_id(task_id)

    def _ensure_model_exists(self, model_id: UUID):
        if not self.model_repo.get_model_by_id(model_id):
            raise HTTPException(status_code=400, detail=f"Model with id={model_id} does not exist")

    def _ensure_dataset_exists(self, dataset_id: UUID):
        if not self.dataset_repo.get_dataset_by_id(dataset_id):
            raise HTTPException(status_code=400, detail=f"Dataset with id={dataset_id} does not exist")

    def _publish(self, queue: QueueTypes, message: dict):
        self.publisher.publish(queue, message)