from typing import Optional
from uuid import UUID

from app.config import settings
from app.core import entities
from app.core.enums import ModelStatus
from app.core.interfaces import ModelInterface, StorageInterface
from app.presentation.schemas import ModelCreate


class ModelService:
    def __init__(self, model_repo: ModelInterface, storage: StorageInterface):
        self.model_repo = model_repo
        self.storage = storage

    def create_model(self,  model: ModelCreate, file_data: bytes, filename: str, content_type: str) -> entities.Model:
        model_object = self.storage.upload_file(file_data, filename, content_type,
                                                settings.MINIO_MODELS_BUCKET)
        model.minio_model_path = model_object
        return self.model_repo.create_model(model)

    def get_model_by_id(self, model_id: UUID) -> Optional[entities.Model]:
        return self.model_repo.get_model_by_id(model_id)

    def get_models(self, skip: int = 0, limit: int = 100, status: Optional[ModelStatus] = None, dataset_id: Optional[UUID] = None) -> list[entities.Model]:
        return self.model_repo.get_models(skip, limit, status, dataset_id)

    def get_models_by_dataset_id(self, dataset_id: UUID) -> list[entities.Model]:
        return self.model_repo.get_models_by_dataset_id(dataset_id)

    def delete_model_by_id(self, model_id: UUID) -> None:
        self.model_repo.delete_model_by_id(model_id)