from datetime import timezone, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import entities
from app.core.enums import QueueTypes, TaskStatus, CacheKeysList, CacheTTL, CacheKeysObject
from app.core.interfaces import ITaskRepository, IStorageRepository, IModelRepository, IDatasetRepository, \
    ICacheRepository
from app.config import settings
from app.infrastructure.mappers import EntityJsonMapper
from app.infrastructure.messaging import RabbitMQPublisher
from app.presentation.schemas import TaskCreate, TaskRead


class TaskService:
    def __init__(self, task_repo: ITaskRepository, storage: IStorageRepository, model_repo: IModelRepository, dataset_repo: IDatasetRepository, cache_repo: ICacheRepository):
        self.task_repo = task_repo
        self.storage = storage
        self.model_repo = model_repo
        self.dataset_repo = dataset_repo
        self.publisher = RabbitMQPublisher()
        self.cache_repo = cache_repo

    async def create_inference_task(self, session: AsyncSession, task: TaskCreate, file_data: bytes, filename: str, content_type: str, current_user: entities.User) -> entities.Task:
        await self._ensure_model_exists(session, task.model_id)

        allowed_types = ["image/jpeg", "image/png", "application/pdf"]
        if content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}.")

        filepath = f"{str(current_user.id)}/{filename}"

        input_object_path = await self.storage.upload_file(file_data, filepath, content_type, settings.MINIO_SCHEMAS_BUCKET)
        task.input_path = input_object_path
        created = await self.task_repo.create_inference_task(session, task)
        model = await self.model_repo.get_model_by_id(session, task.model_id)

        message = {
            "task_id": str(created.id),
            "task_type": TaskStatus.inference,
            "model_id": str(task.model_id),
            "model_arch": model.architecture if hasattr(model, "architecture") else None,
            "input_path": input_object_path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await self._publish(QueueTypes.inference_queue, message)
        await self.cache_repo.delete(CacheKeysObject.task(task_id=created.id))
        await self.cache_repo.delete(CacheKeysList.tasks(user_id=current_user.id))
        return created

    async def create_training_task(self, session: AsyncSession, task: TaskCreate) -> entities.Task:
        await self._ensure_model_exists(session, task.model_id)

        if task.dataset_id:
            await self._ensure_dataset_exists(session, task.dataset_id)

        created = await self.task_repo.create_training_task(session, task)
        model = await self.model_repo.get_model_by_id(session, task.model_id)

        message = {
            "task_id": str(created.id),
            "task_type": TaskStatus.training,
            "model_id": str(task.model_id),
            "model_arch": model.architecture if hasattr(model, "architecture") else None,
            "dataset_id": str(task.dataset_id) if task.dataset_id else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await self._publish(QueueTypes.training_queue, message)
        cache_key = CacheKeysObject.task(task_id=created.id)
        await self.cache_repo.delete(cache_key)
        return created

    async def get_task_by_id(self, session: AsyncSession, task_id: UUID, current_user: entities.User) -> entities.Task:
        cache_key = CacheKeysObject.task(task_id=task_id)
        cached_task = await self.cache_repo.get(cache_key)
        if cached_task:
            return EntityJsonMapper.from_json(cached_task, entities.Task)
        task = await self.task_repo.get_task_by_id(session,task_id)
        if not task:
            raise HTTPException(404, f"Task {task_id} does not exist")

        if task.user_id != current_user.id:
            raise HTTPException(403, "Access denied")
        task_schema = EntityJsonMapper.to_json(task, TaskRead)
        await self.cache_repo.set(cache_key, task_schema, expire=CacheTTL.TASKS.value)

        return task

    async def get_tasks(self, session: AsyncSession, current_user: entities.User, skip: int = 0, limit: int = 100) -> list[entities.Task]:
        cache_key = CacheKeysList.tasks(user_id=current_user.id)
        cached_tasks = await self.cache_repo.get(cache_key)
        if cached_tasks:
            return EntityJsonMapper.from_json(cached_tasks, entities.Task, as_list=True)
        tasks = await self.task_repo.get_tasks(session, skip, limit, user_id=current_user.id)
        tasks_schema = EntityJsonMapper.to_json(tasks, TaskRead)
        await self.cache_repo.set(cache_key, tasks_schema, expire=CacheTTL.TASKS.value)
        return tasks

    # TODO: подумать зачем вообще эта ручка, она вообще вроде как не нужна
    async def get_tasks_by_user_id(self, session: AsyncSession, user_id: UUID) -> list[entities.Task]:
        return await self.task_repo.get_tasks_by_user_id(session, user_id)

    async def delete_task_by_id(self, session: AsyncSession, task_id: UUID, current_user:entities.User) -> None:
        task = await self.task_repo.get_task_by_id(session, task_id)
        if not task:
            raise HTTPException(404, f"Task {task_id} does not exist")

        if task.user_id != current_user.id:
            raise HTTPException(403, "Access denied")

        await self.task_repo.delete_task_by_id(session, task_id)
        cache_key = CacheKeysObject.task(task_id=task_id)
        await self.cache_repo.delete(cache_key)


    async def _ensure_model_exists(self, session: AsyncSession, model_id: UUID):
        if not await self.model_repo.get_model_by_id(session, model_id):
            raise HTTPException(status_code=400, detail=f"Model with id={model_id} does not exist")

    async def _ensure_dataset_exists(self, session: AsyncSession, dataset_id: UUID):
        if not await self.dataset_repo.get_dataset_by_id(session, dataset_id):
            raise HTTPException(status_code=400, detail=f"Dataset with id={dataset_id} does not exist")

    async def _publish(self, queue: QueueTypes, message: dict):
        await self.publisher.publish(queue, message)