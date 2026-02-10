import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.core.enums import TaskStatus


class TaskBase(BaseModel):
    task_type: str
    task_status: TaskStatus = TaskStatus.queued
    model_id: Optional[uuid.UUID] = None
    dataset_id: Optional[uuid.UUID] = None
    input_path: Optional[str] = None
    output_path: Optional[str] = None
    error_msg: Optional[str] = None


class TaskCreate(TaskBase):
    user_id: uuid.UUID


class TaskRead(TaskBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
