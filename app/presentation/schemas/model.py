import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict



class ModelBase(BaseModel):
    name: str
    architecture: str
    architecture_profile: str
    minio_model_path: Optional[str] = None  # просто потому что путь к minio появляется в сервисе после загрузки модели


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
