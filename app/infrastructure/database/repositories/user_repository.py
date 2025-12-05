from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.entities import Dataset, Model, User
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
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[EntityUser]:
        query = select(models.User).where(email == models.User.email)
        result = await db.execute(query)
        db_user = result.scalar_one_or_none()
        return OrmEntityMapper.to_entity(db_user, EntityUser) if db_user else None

    async def create_user(self, db: AsyncSession, user: schemas.UserCreate) -> User | None:
        hashed_password = pwd_context.hash(user.password)
        db_user = models.User(
            email=user.email,
            hashed_password=hashed_password,
            role = UserRole.user
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return OrmEntityMapper.to_entity(db_user, EntityUser)

    async def get_user_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[EntityUser]:
        query = select(models.User).where(user_id == models.User.id)
        result = await db.execute(query)
        db_user = result.scalar_one_or_none()
        return OrmEntityMapper.to_entity(db_user, EntityUser) if db_user else None

    async def get_user_datasets(self, db: AsyncSession, user_id: UUID) -> list[Dataset | None]:
        query = (
            select(models.Dataset)
            .where(user_id == models.Dataset.user_id)
        )
        result = await db.execute(query)
        db_datasets = result.scalars().all()
        return [OrmEntityMapper.to_entity(d, EntityDataset) for d in db_datasets]

    async def get_user_models(self, db: AsyncSession, user_id: UUID) -> list[Model | None]:
        query = (
            select(models.Model)
            .where(
                user_id == models.Model.user_id,
                models.Model.is_system.is_(False)
            )
        )
        result = await db.execute(query)
        db_models = result.scalars().all()
        return [OrmEntityMapper.to_entity(m, EntityModel) for m in db_models]

