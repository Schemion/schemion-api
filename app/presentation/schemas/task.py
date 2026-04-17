import uuid
from typing import Optional

from fastapi import Form
from pydantic import BaseModel, ConfigDict

from app.core.enums import TaskStatus


class TaskBase(BaseModel):
    task_type: str
    status: TaskStatus = TaskStatus.queued
    model_id: Optional[uuid.UUID] = None
    dataset_id: Optional[uuid.UUID] = None
    image_size: Optional[int] = None
    epochs: Optional[int] = None
    name: Optional[str] = None
    input_path: Optional[str] = None
    output_path: Optional[str] = None
    error_msg: Optional[str] = None


class TaskCreate(TaskBase):
    user_id: uuid.UUID


class TaskRead(TaskBase):
    id: uuid.UUID
    user_id: uuid.UUID
    output_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InferenceTaskCreateRequest(BaseModel):
    model_id: uuid.UUID

    @classmethod
    def as_form(cls, model_id: uuid.UUID = Form(...)) -> "InferenceTaskCreateRequest":
        return cls(model_id=model_id)


class TrainingTaskCreateRequest(BaseModel):
    model_id: uuid.UUID
    dataset_id: uuid.UUID
    image_size: int
    num_epochs: int
    name: str

    @classmethod
    def as_form(
        cls,
        model_id: uuid.UUID = Form(...),
        dataset_id: uuid.UUID = Form(...),
        image_size: int = Form(...),
        num_epochs: int = Form(...),
        name: str = Form(...),
    ) -> "TrainingTaskCreateRequest":
        return cls(
            model_id=model_id,
            dataset_id=dataset_id,
            image_size=image_size,
            num_epochs=num_epochs,
            name=name,
        )


class TaskListRequest(BaseModel):
    skip: int = 0
    limit: int = 100
