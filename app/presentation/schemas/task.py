import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TaskBase(BaseModel):
    task_type: str
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
