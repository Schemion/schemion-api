from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.interfaces import ITaskRepository
from app.infrastructure.database import models
from app.infrastructure.mappers import OrmEntityMapper
from app.presentation import schemas
from app.core.entities.task import Task as EntityTask


class TaskRepository(ITaskRepository):

    async def create_inference_task(self, db: AsyncSession, task: schemas.TaskCreate) -> EntityTask:
        db_task = models.Task(
            user_id=task.user_id,
            task_type=task.task_type,
            model_id=task.model_id,
            dataset_id=task.dataset_id,
            input_path=task.input_path,
            output_path=task.output_path,
            error_msg=task.error_msg,
        )
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        return OrmEntityMapper.to_entity(db_task, EntityTask)

    async def create_training_task(self, db: AsyncSession, task: schemas.TaskCreate) -> EntityTask:
        db_task = models.Task(
            user_id=task.user_id,
            task_type=task.task_type,
            model_id=task.model_id,
            dataset_id=task.dataset_id,
            input_path=None,
            output_path=None,
            error_msg=None,
        )
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        return OrmEntityMapper.to_entity(db_task, EntityTask)

    async def get_task_by_id(self, db: AsyncSession, task_id: UUID) -> Optional[EntityTask]:
        query = select(models.Task).where(task_id == models.Task.id)
        result = await db.execute(query)
        db_task = result.scalar_one_or_none()
        return OrmEntityMapper.to_entity(db_task, EntityTask) if db_task else None

    async def get_tasks(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
        model_id: Optional[UUID] = None,
    ) -> list[EntityTask]:

        query = select(models.Task)

        if user_id:
            query = query.where(user_id == models.Task.user_id)
        if model_id:
            query = query.where(model_id == models.Task.model_id)

        result = await db.execute(query)
        db_tasks = result.scalars().all()
        return [OrmEntityMapper.to_entity(task, EntityTask) for task in db_tasks]

    async def get_tasks_by_user_id(self, db: AsyncSession, user_id: UUID) -> list[EntityTask]:
        query = select(models.Task).where(user_id == models.Task.user_id)

        result = await db.execute(query)
        db_tasks = result.scalars().all()
        return [OrmEntityMapper.to_entity(task, EntityTask) for task in db_tasks]

    async def delete_task_by_id(self, db: AsyncSession, task_id: UUID) -> None:
        query = select(models.Task).where(task_id == models.Task.id)
        result = await db.execute(query)
        db_task = result.scalar_one_or_none()
        if db_task:
            await db.delete(db_task)
            await db.commit()
