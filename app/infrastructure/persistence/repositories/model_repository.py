from typing import Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ModelStatus
from app.core.interfaces import IModelRepository
from app.infrastructure.persistence.models import Model
from app.presentation import schemas


class ModelRepository(IModelRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_model(self, model: schemas.ModelCreate, user_id: UUID,
                           is_system: bool = False) -> Model | None:
        db_model = Model(
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
        self.session.add(db_model)
        await self.session.commit()
        await self.session.refresh(db_model)
        return db_model

    async def get_model_by_id(self, model_id: UUID, user_id: Optional[UUID] = None) -> Optional[Model]:
        query = select(Model).where(model_id == Model.id)

        if user_id:
            query = query.where(or_(Model.is_system == True, Model.user_id == user_id))

        result = await self.session.execute(query)
        db_model = result.scalar_one_or_none()
        return db_model

    async def get_models(self, user_id: UUID, skip: int = 0, limit: int = 100,
                         status: Optional[ModelStatus] = None, dataset_id: Optional[UUID] = None,
                         include_system: bool = True
                         ) -> list[Model | None]:
        query = select(Model).where(
            (Model.user_id == user_id) |
            (Model.is_system.is_(True) if include_system else False)
        )
        if status is not None:
            query = query.where(status == Model.status)
        if dataset_id is not None:
            query = query.where(dataset_id == Model.dataset_id)

        query = query.order_by(Model.id)
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        db_models = result.scalars().all()
        return [model for model in db_models]

    async def get_models_by_dataset_id(self, dataset_id: UUID, user_id: UUID) -> list[Model]:
        query = (select(Model)
                 .where(dataset_id == Model.dataset_id,
                        or_(
                            Model.is_system == True,
                            Model.user_id == user_id
                        ))
                 )
        result = await self.session.execute(query)
        db_models = result.scalars().all()
        return [model for model in db_models]

    async def delete_model_by_id(self, model_id: UUID, user_id: UUID) -> None:
        query = select(Model).where(model_id == Model.id, user_id == Model.user_id, Model.is_system.is_(False))
        result = await self.session.execute(query)
        db_model = result.scalar_one_or_none()
        if db_model:
            await self.session.delete(db_model)
            await self.session.commit()
        else:
            raise PermissionError("Model not found")
