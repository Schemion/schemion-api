import uuid
from typing import Optional

from fastapi import Form
from pydantic import BaseModel, ConfigDict


class DatasetBase(BaseModel):
    name: str
    minio_path: Optional[str] = None  # тоже остается опциональным так как потом добавляется в сервисе
    description: Optional[str] = None


class DatasetCreate(DatasetBase):
    pass


class DatasetRead(DatasetBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)


class DatasetCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        description: Optional[str] = Form(None),
    ) -> "DatasetCreateRequest":
        return cls(name=name, description=description)


class DatasetListRequest(BaseModel):
    skip: int = 0
    limit: int = 100
    name_contains: Optional[str] = None
