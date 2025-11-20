from typing import Optional
from uuid import UUID

from fastapi import HTTPException

from app.config import settings
from app.core import entities
from app.core.enums import ModelStatus
from app.core.interfaces import IModelRepository, IStorageRepository, IDatasetRepository
from app.presentation.schemas import ModelCreate


class ModelService:
    def __init__(self, model_repo: IModelRepository, storage: IStorageRepository, dataset_repo: IDatasetRepository):
        self.model_repo = model_repo
        self.dataset_repo = dataset_repo
        self.storage = storage

    def create_model(self,  model: ModelCreate, file_data: bytes, filename: str, content_type: str, current_user: entities.User) -> entities.Model:
        if not file_data:
            raise HTTPException(400, "Uploaded model file is empty")

        if model.dataset_id:
            self._ensure_dataset_exists(model.dataset_id, current_user.id)

        file_path = f"{str(current_user.id)}/{filename}"

        model_object = self.storage.upload_file(file_data, file_path, content_type,
                                                settings.MINIO_MODELS_BUCKET)

        model.minio_model_path = model_object
        return self.model_repo.create_model(model, current_user.id, is_system=False)

    def get_model_by_id(self, model_id: UUID, current_user: entities.User) -> Optional[entities.Model]:
        return self.model_repo.get_model_by_id(model_id, current_user.id)

    def get_models(self, current_user: entities.User, skip: int = 0, limit: int = 100, status: Optional[ModelStatus] = None, dataset_id: Optional[UUID] = None, include_system: bool = True) -> list[entities.Model]:
        return self.model_repo.get_models(user_id=current_user.id, skip=skip, limit=limit, status=status, dataset_id=dataset_id, include_system=include_system)

    def get_models_by_dataset_id(self, dataset_id: UUID, current_user: entities.User) -> list[entities.Model]:
        self._ensure_dataset_exists(dataset_id, current_user.id)

        return self.model_repo.get_models_by_dataset_id(dataset_id=dataset_id, user_id=current_user.id)

    def delete_model_by_id(self, model_id: UUID, current_user: entities.User) -> None:
        model = self._ensure_model_exists(model_id, current_user.id)

        if model.is_system:
            raise HTTPException(403, "Cannot delete system model")

        self.storage.delete_file(model.minio_model_path, settings.MINIO_MODELS_BUCKET)
        self.model_repo.delete_model_by_id(model_id, current_user.id)

    def _ensure_dataset_exists(self, dataset_id: UUID, user_id: UUID):
        dataset = self.dataset_repo.get_dataset_by_id(dataset_id, user_id)
        if not dataset:
            raise HTTPException(status_code=400, detail=f"Dataset with id={dataset_id} does not exist or access denied")

    def _ensure_model_exists(self, model_id: UUID, user_id: UUID):
        model = self.model_repo.get_model_by_id(model_id, user_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model with id={model_id} not found or access denied")
        return model