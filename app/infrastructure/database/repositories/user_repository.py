from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from sqlalchemy.orm import selectinload

from app.core.enums import UserRole
from app.infrastructure.database import models
from app.presentation import schemas
from app.core.interfaces.user_interface import IUserRepository
from passlib.context import CryptContext
from app.infrastructure.database.models import User, Dataset, Model


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> Optional[User]:
        query = select(models.User).where(email == models.User.email).options(selectinload(models.User.user_roles).selectinload(models.UserRole.role))
        result = await self.session.execute(query)
        db_user = result.scalar_one_or_none()
        return db_user if db_user else None

    async def create_user(self, user: schemas.UserCreate) -> User | None:
        hashed_password = pwd_context.hash(user.password)
        db_user = models.User(
            email=user.email,
            hashed_password=hashed_password,
        )
        result = await self.session.execute(
            select(models.Role).where(models.Role.name == UserRole.user.value)
        )
        default_role = result.scalar_one()
        db_user.user_roles.append(models.UserRole(role=default_role))
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        query = select(models.User).where(user_id == models.User.id).options(selectinload(models.User.user_roles).selectinload(models.UserRole.role))
        result = await self.session.execute(query)
        db_user = result.scalar_one_or_none()
        return db_user if db_user else None

    async def get_user_datasets(self, user_id: UUID) -> list[Dataset]:
        query = (
            select(models.Dataset)
            .where(user_id == models.Dataset.user_id)
        )
        result = await self.session.execute(query)
        db_datasets = result.scalars().all()
        return [dataset for dataset in db_datasets]

    async def get_user_models(self, user_id: UUID) -> list[Model]:
        query = (
            select(models.Model)
            .where(
                user_id == models.Model.user_id,
                models.Model.is_system.is_(False)
            )
        )
        result = await self.session.execute(query)
        db_models = result.scalars().all()
        return [model for model in db_models]

