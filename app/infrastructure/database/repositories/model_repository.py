from uuid import UUID

from sqlalchemy.orm import Session
from typing import Optional

from app.core.enums import ModelStatus
from app.core.interfaces import ModelInterface
from app.infrastructure.database import models
from app.presentation import schemas
from app.core.entities.model import Model as EntityModel


class ModelRepository(ModelInterface):
    def __init__(self, db: Session):
        self.db = db

    def create_model(self, model: schemas.ModelCreate) -> EntityModel:
        db_model = models.Model(
            name=model.name,
            version=model.version,
            architecture=model.architecture,
            dataset_id=model.dataset_id,
            minio_model_path=model.minio_model_path,
            status=model.status or ModelStatus.pending,
        )
        self.db.add(db_model)
        self.db.commit()
        self.db.refresh(db_model)
        return self._to_entity(db_model)

    def get_model_by_id(self, model_id: UUID) -> Optional[EntityModel]:
        db_model = self.db.query(models.Model).filter(model_id == models.Model.id).first()
        return self._to_entity(db_model) if db_model else None

    def get_models(
            self,
            skip: int = 0,
            limit: int = 100,
            status: Optional[ModelStatus] = None,
            dataset_id: Optional[UUID] = None,
    ) -> list[EntityModel]:
        query = self.db.query(models.Model)

        if status is not None:
            query = query.filter(status == models.Model.status)
        if dataset_id is not None:
            query = query.filter(dataset_id == models.Model.dataset_id)

        db_models = query.offset(skip).limit(limit).all()
        return [self._to_entity(model) for model in db_models]

    def get_models_by_dataset_id(self, dataset_id: UUID) -> list[EntityModel]:
        db_models = (
            self.db.query(models.Model)
            .filter(dataset_id == models.Model.dataset_id)
            .all()
        )
        return [self._to_entity(model) for model in db_models]

    def delete_model_by_id(self, model_id: UUID) -> None:
        db_model = self.db.query(models.Model).filter(model_id == models.Model.id).first()
        if db_model:
            self.db.delete(db_model)
            self.db.commit()

    @staticmethod
    def _to_entity(db_model: models.Model) -> EntityModel:
        return EntityModel(
            id=db_model.id,
            name=db_model.name,
            version=db_model.version,
            architecture = db_model.architecture,
            dataset_id=db_model.dataset_id,
            minio_model_path=db_model.minio_model_path,
            status=db_model.status,
            created_at=db_model.created_at,
        )

    @staticmethod
    def _to_orm(entity: EntityModel) -> models.Model:
        return EntityModel(
            id=entity.id,
            name=entity.name,
            version=entity.version,
            architecture=entity.architecture,
            dataset_id=entity.dataset_id,
            minio_model_path=entity.minio_model_path,
            status=entity.status,
            created_at=entity.created_at,
        )