from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional
from app.core.interfaces import ITaskRepository
from app.infrastructure.database import models
from app.infrastructure.mappers import OrmEntityMapper
from app.presentation import schemas
from app.core.entities.task import Task as EntityTask


class TaskRepository(ITaskRepository):
    def __init__(self, db: Session):
        self.db = db

    def create_inference_task(self, task: schemas.TaskCreate) -> EntityTask:
        db_task = models.Task(
            user_id=task.user_id,
            task_type=task.task_type,
            model_id=task.model_id,
            dataset_id=task.dataset_id,
            input_path=task.input_path,
            output_path=task.output_path,
            error_msg=task.error_msg,
        )
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return OrmEntityMapper.to_entity(db_task, EntityTask)

    def create_training_task(self, task: schemas.TaskCreate) -> EntityTask:
        db_task = models.Task(
            user_id=task.user_id,
            task_type=task.task_type,
            model_id=task.model_id,
            dataset_id=task.dataset_id,
            input_path=None,
            output_path=None,
            error_msg=None,
        )
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return OrmEntityMapper.to_entity(db_task, EntityTask)

    def get_task_by_id(self, task_id: UUID) -> Optional[EntityTask]:
        db_task = self.db.query(models.Task).filter(task_id == models.Task.id).first()
        return OrmEntityMapper.to_entity(db_task, EntityTask) if db_task else None

    def get_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
        model_id: Optional[UUID] = None,
    ) -> list[EntityTask]:

        query = self.db.query(models.Task)

        if user_id:
            query = query.filter(user_id == models.Task.user_id)
        if model_id:
            query = query.filter(model_id == models.Task.model_id)

        db_tasks = query.offset(skip).limit(limit).all()
        return [OrmEntityMapper.to_entity(task, EntityTask) for task in db_tasks]

    def get_tasks_by_user_id(self, user_id: UUID) -> list[EntityTask]:
        db_tasks = self.db.query(models.Task).filter(user_id == models.Task.user_id).all()
        return [OrmEntityMapper.to_entity(task, EntityTask) for task in db_tasks]

    def delete_task_by_id(self, task_id: UUID) -> None:
        self.db.query(models.Task).filter(task_id == models.Task.id).delete()
        self.db.commit()
