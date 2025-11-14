from uuid import UUID

from sqlalchemy.orm import Session
from typing import Optional

from app.core.interfaces import IDatasetRepository
from app.infrastructure.database import models
from app.infrastructure.mappers import OrmEntityMapper
from app.presentation import schemas
from app.core.entities.dataset import Dataset as EntityDataset

class DatasetRepository(IDatasetRepository):
    def __init__(self, db: Session):
        self.db = db

    def create_dataset(self, dataset: schemas.DatasetCreate, user_id: UUID) -> EntityDataset:
        db_dataset = models.Dataset(
            user_id = user_id,
            name=dataset.name,
            minio_path=dataset.minio_path,
            description=dataset.description,
            num_samples=dataset.num_samples or 0,
        )
        self.db.add(db_dataset)
        self.db.commit()
        self.db.refresh(db_dataset)
        return OrmEntityMapper.to_entity(db_dataset, EntityDataset)

    def get_dataset_by_id(self, dataset_id: UUID, user_id: Optional[UUID] = None) -> Optional[EntityDataset]:
        query = self.db.query(models.Dataset).filter(dataset_id == models.Dataset.id)

        if user_id:
            query = query.filter((models.Dataset.user_id == user_id) | (models.Dataset.user_id.is_(None)))

        db_dataset = query.first()

        return OrmEntityMapper.to_entity(db_dataset, EntityDataset) if db_dataset else None

    def get_datasets(self, user_id: UUID, skip: int = 0, limit: int = 100, name_contains: Optional[str] = None) -> list[EntityDataset]:
        query = self.db.query(models.Dataset).filter((models.Dataset.user_id == user_id) | (models.Dataset.user_id.is_(None)))

        if name_contains:
            query = query.filter(models.Dataset.name.ilike(f"%{name_contains}%"))

        db_datasets = query.offset(skip).limit(limit).all()
        return [OrmEntityMapper.to_entity(dataset, EntityDataset) for dataset in db_datasets]

    def delete_dataset_by_id(self, dataset_id: UUID) -> None:
        db_dataset = self.db.query(models.Dataset).filter(dataset_id == models.Dataset.id).first()
        if db_dataset:
            self.db.delete(db_dataset)
            self.db.commit()
