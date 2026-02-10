from datetime import datetime, timezone
from uuid import UUID


from app.core.enums import CacheKeysList, CacheKeysObject, CacheTTL, QueueTypes, TaskType
from app.core.exceptions import NotFoundError, ValidationError
from app.core.interfaces import ICacheRepository, IDatasetRepository, IModelRepository, IStorageRepository, \
    ITaskRepository
from app.infrastructure.config import settings
from app.infrastructure.messaging import RabbitMQPublisher
from app.presentation.schemas import TaskCreate, TaskRead


class TaskService:
    def __init__(self, task_repo: ITaskRepository, storage: IStorageRepository, model_repo: IModelRepository,
                 dataset_repo: IDatasetRepository, cache_repo: ICacheRepository):
        self.task_repo = task_repo
        self.storage = storage
        self.model_repo = model_repo
        self.dataset_repo = dataset_repo
        self.publisher = RabbitMQPublisher()
        self.cache_repo = cache_repo

    async def create_inference_task(self, task: TaskCreate, file_data: bytes, filename: str,
                                    content_type: str, user_id: UUID) -> TaskRead:
        if task.model_id:
            await self._ensure_model_exists(task.model_id)
        else:
            raise NotFoundError(f"Model ID does not exist: {task.model_id}.")

        allowed_types = ["image/jpeg", "image/png", "application/pdf"]
        if content_type not in allowed_types:
            raise ValidationError(f"Unsupported file type: {content_type}. Allowed: {allowed_types}")

        filepath = f"{str(user_id)}/{filename}"

        input_object_path = await self.storage.upload_file(file_data, filepath, content_type,
                                                           settings.MINIO_SCHEMAS_BUCKET)
        task.input_path = input_object_path
        created = await self.task_repo.create_inference_task(task)
        model = await self.model_repo.get_model_by_id(task.model_id)

        message = {
            "task_id":    str(created.id),
            "task_type":  TaskType.inference,
            "model_id":   str(task.model_id),
            "model_arch": model.architecture if hasattr(model, "architecture") else None,
            "input_path": input_object_path,
            "timestamp":  datetime.now(timezone.utc).isoformat()
        }

        await self._publish(QueueTypes.inference_queue, message)
        await self.cache_repo.delete(CacheKeysObject.task(task_id=created.id))
        await self.cache_repo.delete(CacheKeysList.tasks(user_id=user_id))
        return created

    async def create_training_task(self, task: TaskCreate) -> TaskRead:
        if task.dataset_id:
            await self._ensure_dataset_exists(task.dataset_id)
        created = await self.task_repo.create_training_task(task)

        message = {
            "task_id":    str(created.id),
            "task_type":  TaskType.training,
            "model_id":   str(task.model_id),
            "dataset_id": str(task.dataset_id),
            "timestamp":  datetime.now(timezone.utc).isoformat()
        }

        await self._publish(QueueTypes.training_queue, message)
        cache_key = CacheKeysObject.task(task_id=created.id)
        await self.cache_repo.delete(cache_key)
        return created

    async def get_task_by_id(self, task_id: UUID, user_id: UUID) -> TaskRead:
        cache_key = CacheKeysObject.task(task_id=task_id)
        cached = await self.cache_repo.get(cache_key)
        if cached:
            return TaskRead(**cached)

        task = await self.task_repo.get_task_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task with id {task_id} does not exist")

        if task.user_id != user_id:
            raise PermissionError("Access denied")
        await self.cache_repo.set(cache_key, TaskRead.model_validate(task).model_dump(), expire=CacheTTL.TASKS.value)

        return task

    async def get_tasks(self, user_id: UUID, skip: int = 0, limit: int = 100) -> \
            list[TaskRead]:
        cache_key = CacheKeysList.tasks(user_id=user_id)
        cached = await self.cache_repo.get(cache_key)
        if cached:
            return [TaskRead(**item) for item in cached]
        tasks = await self.task_repo.get_tasks(skip, limit, user_id=user_id)

        serialized = [TaskRead.model_validate(task).model_dump() for task in tasks]

        await self.cache_repo.set(cache_key, serialized, expire=CacheTTL.TASKS.value)
        return tasks

    async def delete_task_by_id(self, task_id: UUID, user_id: UUID) -> None:
        task = await self.task_repo.get_task_by_id(task_id)
        if not task:
            raise NotFoundError(f"Task with id {task_id} does not exist")

        if task.user_id != user_id:
            raise PermissionError("Access denied")

        await self.task_repo.delete_task_by_id(task_id)
        cache_key = CacheKeysObject.task(task_id=task_id)
        await self.cache_repo.delete_pattern(cache_key)

    async def _ensure_model_exists(self, model_id: UUID):
        if not await self.model_repo.get_model_by_id(model_id):
            raise NotFoundError(f"Model with id {model_id} does not exist")

    async def _ensure_dataset_exists(self, dataset_id: UUID):
        if not await self.dataset_repo.get_dataset_by_id(dataset_id):
            raise NotFoundError(f"Dataset with id {dataset_id} does not exist")

    async def _publish(self, queue: QueueTypes, message: dict):
        await self.publisher.publish(queue, message)
