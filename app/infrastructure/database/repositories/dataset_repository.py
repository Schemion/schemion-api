from uuid import UUID

from sqlalchemy.orm import Session
from typing import Optional

from app.core.interfaces import DatasetInterface
from app.infrastructure.database import models
from app.infrastructure.mappers import OrmEntityMapper
from app.presentation import schemas
from app.core.entities.dataset import Dataset as EntityDataset

class DatasetRepository(DatasetInterface):
    def __init__(self, db: Session):
        self.db = db

    def create_dataset(self, dataset: schemas.DatasetCreate) -> EntityDataset:
        db_dataset = models.Dataset(
            name=dataset.name,
            minio_path=dataset.minio_path,
            description=dataset.description,
            num_samples=dataset.num_samples or 0,
        )
        self.db.add(db_dataset)
        self.db.commit()
        self.db.refresh(db_dataset)
        return OrmEntityMapper.to_entity(db_dataset, EntityDataset)

    def get_dataset_by_id(self, dataset_id: UUID) -> Optional[EntityDataset]:
        db_dataset = self.db.query(models.Dataset).filter(dataset_id == models.Dataset.id).first()
        return OrmEntityMapper.to_entity(db_dataset, EntityDataset) if db_dataset else None

    def get_datasets(self, skip: int = 0, limit: int = 100, name_contains: Optional[str] = None) -> list[EntityDataset]:
        query = self.db.query(models.Dataset)

        if name_contains:
            query = query.filter(models.Dataset.name.ilike(f"%{name_contains}%"))

        db_datasets = query.offset(skip).limit(limit).all()
        return [OrmEntityMapper.to_entity(dataset, EntityDataset) for dataset in db_datasets]

    def delete_dataset_by_id(self, dataset_id: UUID) -> None:
        db_dataset = self.db.query(models.Dataset).filter(dataset_id == models.Dataset.id).first()
        if db_dataset:
            self.db.delete(db_dataset)
            self.db.commit()
