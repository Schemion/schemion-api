from uuid import UUID
from sqlalchemy import and_
from sqlalchemy.orm import Session
from typing import Optional
from app.core.interfaces import TaskInterface
from app.infrastructure.database import models
from app.presentation import schemas
from app.core.entities.task import Task as EntityTask


class TaskRepository(TaskInterface):
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, task: schemas.TaskCreate) -> EntityTask:
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
        return self._to_entity(db_task)

    def get_task_by_id(self, task_id: UUID) -> Optional[EntityTask]:
        db_task = self.db.query(models.Task).filter(models.Task.id == task_id).first()
        return self._to_entity(db_task) if db_task else None

    def get_tasks(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None, model_id: Optional[UUID] = None) -> list[EntityTask]:
        query = self.db.query(models.Task)

        filters = []
        if user_id is not None:
            filters.append(models.Task.user_id == user_id)
        if model_id is not None:
            filters.append(models.Task.model_id == model_id)

        if filters:
            query = query.filter(and_(*filters))

        db_tasks = query.offset(skip).limit(limit).all()
        return [self._to_entity(task) for task in db_tasks]

    def get_tasks_by_user_id(self, user_id: UUID) -> Optional[list[EntityTask]]:
        db_tasks = self.db.query(models.Task).filter(models.Task.user_id == user_id).all()
        return [self._to_entity(task) for task in db_tasks] if db_tasks else None

    def delete_task_by_id(self, task_id: UUID) -> None:
        db_task = self.db.query(models.Task).filter(models.Task.id == task_id).first()
        if db_task:
            self.db.delete(db_task)
            self.db.commit()

    @staticmethod
    def _to_entity(db_task: models.Task) -> EntityTask:
        return EntityTask(
            id=db_task.id,
            user_id=db_task.user_id,
            task_type=db_task.task_type,
            model_id=db_task.model_id,
            dataset_id=db_task.dataset_id,
            input_path=db_task.input_path,
            output_path=db_task.output_path,
            error_msg=db_task.error_msg,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at,
        )

    @staticmethod
    def _to_orm(entity: EntityTask) -> models.Task:
        return  EntityTask(
            id=entity.id,
            user_id=entity.user_id,
            task_type=entity.task_type,
            model_id=entity.model_id,
            dataset_id=entity.dataset_id,
            input_path=entity.input_path,
            output_path=entity.output_path,
            error_msg=entity.error_msg,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )