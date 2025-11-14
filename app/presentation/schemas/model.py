import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.core.enums import ModelStatus


class ModelBase(BaseModel):
    name: str
    version: str
    architecture: str
    minio_model_path: str
    status: ModelStatus = ModelStatus.pending


class ModelCreate(ModelBase):
    dataset_id: Optional[uuid.UUID] = None
    base_model_id: Optional[uuid.UUID] = None


class ModelRead(ModelBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    is_system: bool
    dataset_id: Optional[uuid.UUID]
    base_model_id: Optional[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)
