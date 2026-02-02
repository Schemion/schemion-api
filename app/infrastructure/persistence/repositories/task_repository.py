from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.interfaces import ITaskRepository
from app.infrastructure.persistence.models import Task
from app.presentation import schemas


class TaskRepository(ITaskRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_inference_task(self, task: schemas.TaskCreate) -> Task | None:
        db_task = Task(
            user_id=task.user_id,
            task_type=task.task_type,
            model_id=task.model_id,
            dataset_id=task.dataset_id,
            input_path=task.input_path,
            output_path=task.output_path,
            error_msg=task.error_msg,
        )
        self.session.add(db_task)
        await self.session.commit()
        await self.session.refresh(db_task)
        return db_task

    async def create_training_task(self, task: schemas.TaskCreate) -> Task | None:
        db_task = Task(
            user_id=task.user_id,
            task_type=task.task_type,
            model_id=task.model_id,
            dataset_id=task.dataset_id,
            input_path=None,
            output_path=None,
            error_msg=None,
        )
        self.session.add(db_task)
        await self.session.commit()
        await self.session.refresh(db_task)
        return db_task

    async def get_task_by_id(self, task_id: UUID) -> Optional[Task]:
        query = select(Task).where(task_id == Task.id)
        result = await self.session.execute(query)
        db_task = result.scalar_one_or_none()
        return db_task if db_task else None

    async def get_tasks(
            self,
            skip: int = 0,
            limit: int = 100,
            user_id: Optional[UUID] = None,
            model_id: Optional[UUID] = None,
    ) -> list[Task | None]:

        query = select(Task)

        if user_id:
            query = query.where(user_id == Task.user_id)
        if model_id:
            query = query.where(model_id == Task.model_id)

        result = await self.session.execute(query)
        db_tasks = result.scalars().all()
        return [task for task in db_tasks]

    async def get_tasks_by_user_id(self, user_id: UUID) -> list[Task]:
        query = select(Task).where(user_id == Task.user_id)

        result = await self.session.execute(query)
        db_tasks = result.scalars().all()
        return [task for task in db_tasks]

    async def delete_task_by_id(self, task_id: UUID) -> None:
        query = select(Task).where(task_id == Task.id)
        result = await self.session.execute(query)
        db_task = result.scalar_one_or_none()
        if db_task:
            await self.session.delete(db_task)
            await self.session.commit()
