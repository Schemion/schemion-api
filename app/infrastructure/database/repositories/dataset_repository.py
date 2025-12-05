from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional

from app.core.entities import Dataset
from app.core.interfaces import IDatasetRepository
from app.infrastructure.database import models
from app.infrastructure.mappers import OrmEntityMapper
from app.presentation import schemas
from app.core.entities.dataset import Dataset as EntityDataset

class DatasetRepository(IDatasetRepository):
    async def create_dataset(self, db: AsyncSession, dataset: schemas.DatasetCreate, user_id: UUID) -> Dataset | None:
        db_dataset = models.Dataset(
            user_id = user_id,
            name=dataset.name,
            minio_path=dataset.minio_path,
            description=dataset.description,
            num_samples=dataset.num_samples or 0,
        )
        db.add(db_dataset)
        await db.commit()
        await db.refresh(db_dataset)
        return OrmEntityMapper.to_entity(db_dataset, EntityDataset)

    async def get_dataset_by_id(self, db: AsyncSession, dataset_id: UUID, user_id: Optional[UUID] = None) -> Optional[EntityDataset]:
        query = select(models.Dataset).where(dataset_id == models.Dataset.id)

        if user_id:
            query = query.where((models.Dataset.user_id == user_id) | (models.Dataset.user_id.is_(None)))

        result = await db.execute(query)
        db_dataset = result.scalar_one_or_none()
        return OrmEntityMapper.to_entity(db_dataset, EntityDataset) if db_dataset else None

    async def get_datasets(self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100, name_contains: Optional[str] = None) -> \
    list[Dataset | None]:
        query = select(models.Dataset).where((models.Dataset.user_id == user_id) | (models.Dataset.user_id.is_(None)))

        if name_contains:
            query = query.where(models.Dataset.name.ilike(f"%{name_contains}%"))

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        db_datasets = result.scalars().all()
        return [OrmEntityMapper.to_entity(dataset, EntityDataset) for dataset in db_datasets]

    async def delete_dataset_by_id(self, db: AsyncSession,  dataset_id: UUID) -> None:
        query = select(models.Dataset).where(dataset_id == models.Dataset.id)
        result = await db.execute(query)
        db_dataset = result.scalar_one_or_none()

        if db_dataset:
            await db.delete(db_dataset)
            await db.commit()
