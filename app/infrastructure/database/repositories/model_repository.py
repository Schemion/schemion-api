from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Optional

from app.core.enums import ModelStatus
from app.core.interfaces import IModelRepository
from app.infrastructure.database import models
from app.infrastructure.mappers import OrmEntityMapper
from app.presentation import schemas
from app.core.entities.model import Model as EntityModel


class ModelRepository(IModelRepository):
    def __init__(self, db: Session):
        self.db = db

    def create_model(self, model: schemas.ModelCreate, user_id: UUID, is_system: bool = False) -> EntityModel:
        db_model = models.Model(
            user_id=user_id if not is_system else None,
            is_system=is_system,
            name=model.name,
            version=model.version,
            architecture=model.architecture,
            architecture_profile=model.architecture_profile,
            dataset_id=model.dataset_id,
            minio_model_path=model.minio_model_path,
            status=model.status or ModelStatus.pending,
            base_model_id=model.base_model_id,
        )
        self.db.add(db_model)
        self.db.commit()
        self.db.refresh(db_model)
        return OrmEntityMapper.to_entity(db_model, EntityModel)

    def get_model_by_id(self, model_id: UUID, user_id: Optional[UUID] = None) -> Optional[EntityModel]:
        query = self.db.query(models.Model).filter(model_id == models.Model.id)

        if user_id:
            query = query.filter(or_(models.Model.is_system == True,models.Model.user_id == user_id))

        db_model = query.first()
        return OrmEntityMapper.to_entity(db_model, EntityModel) if db_model else None

    def get_models(
            self,
            user_id: UUID,
            skip: int = 0,
            limit: int = 100,
            status: Optional[ModelStatus] = None,
            dataset_id: Optional[UUID] = None,
            include_system: bool = True
    ) -> list[EntityModel]:
        query = self.db.query(models.Model).filter(or_(models.Model.is_system == include_system,models.Model.user_id == user_id))

        if status is not None:
            query = query.filter(status == models.Model.status)
        if dataset_id is not None:
            query = query.filter(dataset_id == models.Model.dataset_id)

        db_models = query.offset(skip).limit(limit).all()
        return [OrmEntityMapper.to_entity(model, EntityModel) for model in db_models]

    def get_models_by_dataset_id(self, dataset_id: UUID, user_id: UUID) -> list[EntityModel]:
        db_models = (self.db.query(models.Model)
            .filter(dataset_id == models.Model.dataset_id,
                    or_(
                    models.Model.is_system == True,
                    models.Model.user_id == user_id
                )).all()
        )
        return [OrmEntityMapper.to_entity(model, EntityModel) for model in db_models]

    def delete_model_by_id(self, model_id: UUID, user_id: UUID) -> None:
        db_model = self.db.query(models.Model).filter(model_id == models.Model.id, user_id == models.Model.user_id, False == models.Model.is_system).first()

        if db_model:
            self.db.delete(db_model)
            self.db.commit()
        else:
            raise PermissionError("Model not found or you don't have access")

