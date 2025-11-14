from typing import Optional
from uuid import UUID

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

    def create_model(self,  model: ModelCreate, file_data: bytes, filename: str, content_type: str, current_user: entities.User, is_fine_tune: bool = False) -> entities.Model:
        model_object = self.storage.upload_file(file_data, filename, content_type,
                                                settings.MINIO_MODELS_BUCKET)

        if is_fine_tune and model.base_model_id:
            base_model = self.get_model_by_id(model.base_model_id, current_user)
            if not base_model:
                raise ValueError("Base model not found or you don't have access")

        model.minio_model_path = model_object
        return self.model_repo.create_model(model, current_user.id, is_system=False)

    def get_model_by_id(self, model_id: UUID, current_user: entities.User) -> Optional[entities.Model]:
        return self.model_repo.get_model_by_id(model_id, current_user.id)

    def get_models(self, current_user: entities.User, skip: int = 0, limit: int = 100, status: Optional[ModelStatus] = None, dataset_id: Optional[UUID] = None, include_system: bool = True) -> list[entities.Model]:
        return self.model_repo.get_models(user_id=current_user.id, skip=skip, limit=limit, status=status, dataset_id=dataset_id, include_system=include_system)

    def get_models_by_dataset_id(self, dataset_id: UUID, current_user: entities.User) -> list[entities.Model]:
        dataset = self.dataset_repo.get_dataset_by_id(dataset_id, current_user.id)
        if not dataset:
            raise PermissionError("Dataset not found or access denied")

        return self.model_repo.get_models_by_dataset_id(dataset_id=dataset_id, user_id=current_user.id)

    def delete_model_by_id(self, model_id: UUID, current_user: entities.User) -> None:
        model = self.get_model_by_id(model_id, current_user)
        if not model:
            raise PermissionError("Model not found or access denied")

        if model.is_system:
            raise PermissionError("Cannot delete system model")

        self.storage.delete_file(model.minio_model_path, settings.MINIO_MODELS_BUCKET)
        self.model_repo.delete_model_by_id(model_id, current_user.id)