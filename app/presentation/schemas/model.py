import uuid
from typing import Optional

from fastapi import Form
from pydantic import BaseModel, ConfigDict

from app.core.enums import ModelArchitectures


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


class ModelCreateRequest(BaseModel):
    name: str
    architecture: ModelArchitectures
    architecture_profile: str
    dataset_id: Optional[uuid.UUID] = None

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        architecture: ModelArchitectures = Form(...),
        architecture_profile: str = Form(...),
        dataset_id: Optional[uuid.UUID] = Form(None),
    ) -> "ModelCreateRequest":
        return cls(
            name=name,
            architecture=architecture,
            architecture_profile=architecture_profile,
            dataset_id=dataset_id,
        )


class ModelListRequest(BaseModel):
    skip: int = 0
    limit: int = 100
    dataset_id: Optional[uuid.UUID] = None
    include_system: bool = True
