from uuid import UUID

from sqlalchemy.orm import Session
from typing import Optional

from app.core.interfaces import DatasetInterface
from app.infrastructure.database import models
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
        return self._to_entity(db_dataset)

    def get_dataset_by_id(self, dataset_id: UUID) -> Optional[EntityDataset]:
        db_dataset = self.db.query(models.Dataset).filter(dataset_id == models.Dataset.id).first()
        return self._to_entity(db_dataset) if db_dataset else None

    def get_datasets(self, skip: int = 0, limit: int = 100, name_contains: Optional[str] = None) -> list[EntityDataset]:
        query = self.db.query(models.Dataset)

        if name_contains:
            query = query.filter(models.Dataset.name.ilike(f"%{name_contains}%"))

        db_datasets = query.offset(skip).limit(limit).all()
        return [self._to_entity(dataset) for dataset in db_datasets]

    def delete_dataset_by_id(self, dataset_id: UUID) -> None:
        db_dataset = self.db.query(models.Dataset).filter(dataset_id == models.Dataset.id).first()
        if db_dataset:
            self.db.delete(db_dataset)
            self.db.commit()

    @staticmethod
    def _to_entity(db_dataset: models.Dataset) -> EntityDataset:
        return EntityDataset(
            id=db_dataset.id,
            name=db_dataset.name,
            minio_path=db_dataset.minio_path,
            description=db_dataset.description,
            num_samples=db_dataset.num_samples,
            created_at=db_dataset.created_at,
        )

    @staticmethod
    def _to_orm(entity: EntityDataset) -> models.Dataset:
        return EntityDataset(
            id=entity.id,
            name=entity.name,
            minio_path=entity.minio_path,
            description=entity.description,
            num_samples=entity.num_samples,
            created_at=entity.created_at,
        )