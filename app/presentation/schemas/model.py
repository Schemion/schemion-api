import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.core.enums import ModelStatus


class ModelBase(BaseModel):
    name: str
    version: str
    minio_model_path: Optional[str] = None
    status: ModelStatus = ModelStatus.pending


class ModelCreate(ModelBase):
    dataset_id: Optional[uuid.UUID] = None


class ModelRead(ModelBase):
    id: uuid.UUID
    dataset_id: Optional[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)
