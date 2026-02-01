from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional

from app.core.interfaces import IDatasetRepository
from app.infrastructure.database.models import Dataset
from app.presentation import schemas


class DatasetRepository(IDatasetRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_dataset(self, dataset: schemas.DatasetCreate, user_id: UUID) -> Dataset | None:
        db_dataset = Dataset(
            user_id = user_id,
            name=dataset.name,
            minio_path=dataset.minio_path,
            description=dataset.description,
            num_samples=dataset.num_samples or 0,
        )
        self.session.add(db_dataset)
        await self.session.commit()
        await self.session.refresh(db_dataset)
        return db_dataset

    async def get_dataset_by_id(self, dataset_id: UUID, user_id: Optional[UUID] = None) -> Optional[Dataset]:
        query = select(Dataset).where(dataset_id == Dataset.id)

        if user_id:
            query = query.where((Dataset.user_id == user_id) | (Dataset.user_id.is_(None)))

        result = await self.session.execute(query)
        db_dataset = result.scalar_one_or_none()
        return db_dataset

    async def get_datasets(self, user_id: UUID, skip: int = 0, limit: int = 100, name_contains: Optional[str] = None) -> \
    list[Dataset | None]:
        query = select(Dataset).where((Dataset.user_id == user_id) | (Dataset.user_id.is_(None)))

        if name_contains:
            query = query.where(Dataset.name.ilike(f"%{name_contains}%"))

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        db_datasets = result.scalars().all()
        return [dataset for dataset in db_datasets]

    async def delete_dataset_by_id(self, dataset_id: UUID) -> None:
        query = select(Dataset).where(dataset_id == Dataset.id)
        result = await self.session.execute(query)
        db_dataset = result.scalar_one_or_none()

        if db_dataset:
            await self.session.delete(db_dataset)
            await self.session.commit()