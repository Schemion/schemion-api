import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DatasetBase(BaseModel):
    name: str
    minio_path: Optional[str] = None #  тоже остается опциональным так как потом добавляется в сервисе
    description: Optional[str] = None
    num_samples: int = 0


class DatasetCreate(DatasetBase):
    pass


class DatasetRead(DatasetBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)
