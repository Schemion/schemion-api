from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.enums import UserRole
from app.infrastructure.database import models
from app.presentation import schemas
from app.core.interfaces.user_interface import IUserRepository
from app.core.entities.dataset import Dataset as EntityDataset
from app.core.entities.model import Model as EntityModel
from app.core.entities.user import User as EntityUser
from passlib.context import CryptContext
from app.infrastructure.mappers import OrmEntityMapper


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRepository(IUserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[EntityUser]:
        query = select(models.User).where(email == models.User.email)
        result = await self.db.execute(query)
        db_user = result.scalar_one_or_none()
        return OrmEntityMapper.to_entity(db_user, EntityUser) if db_user else None

    async def create_user(self, user: schemas.UserCreate) -> EntityUser:
        hashed_password = pwd_context.hash(user.password)
        db_user = models.User(
            email=user.email,
            hashed_password=hashed_password,
            role = UserRole.user
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return OrmEntityMapper.to_entity(db_user, EntityUser)

    async def get_user_by_id(self, user_id: UUID) -> Optional[EntityUser]:
        query = select(models.User).where(user_id == models.User.id)
        result = await self.db.execute(query)
        db_user = result.scalar_one_or_none()
        return OrmEntityMapper.to_entity(db_user, EntityUser) if db_user else None

    async def get_user_datasets(self, user_id: UUID) -> List[EntityDataset]:
        query = (
            select(models.Dataset)
            .where(user_id == models.Dataset.user_id)
        )
        result = await self.db.execute(query)
        db_datasets = result.scalars().all()
        return [OrmEntityMapper.to_entity(d, EntityDataset) for d in db_datasets]

    async def get_user_models(self, user_id: UUID) -> List[EntityModel]:
        query = (
            select(models.Model)
            .where(
                user_id == models.Model.user_id,
                models.Model.is_system.is_(False)
            )
        )
        result = await self.db.execute(query)
        db_models = result.scalars().all()
        return [OrmEntityMapper.to_entity(m, EntityModel) for m in db_models]

