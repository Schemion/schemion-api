from typing import Optional
from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import UserRoles
from app.core.interfaces.user_interface import IUserRepository
from app.infrastructure.persistence.models import Dataset, Model, Role, User, UserRole
from app.presentation import schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(email == User.email).options(
            selectinload(User.user_roles).selectinload(UserRole.role))
        result = await self.session.execute(query)
        db_user = result.scalar_one_or_none()
        return db_user if db_user else None

    async def create_user(self, user: schemas.UserCreate) -> User | None:
        hashed_password = pwd_context.hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
        )
        result = await self.session.execute(
            select(Role).where(Role.name == UserRoles.user.value)
        )
        default_role = result.scalar_one()
        db_user.user_roles.append(UserRole(role=default_role))
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        query = select(User).where(user_id == User.id).options(
            selectinload(User.user_roles).selectinload(UserRole.role))
        result = await self.session.execute(query)
        db_user = result.scalar_one_or_none()
        return db_user if db_user else None

    async def get_user_datasets(self, user_id: UUID) -> list[Dataset]:
        query = (
            select(Dataset)
            .where(user_id == Dataset.user_id)
        )
        result = await self.session.execute(query)
        db_datasets = result.scalars().all()
        return [dataset for dataset in db_datasets]

    async def get_user_models(self, user_id: UUID) -> list[Model]:
        query = (
            select(Model)
            .where(
                user_id == Model.user_id,
                Model.is_system.is_(False)
            )
        )
        result = await self.session.execute(query)
        db_models = result.scalars().all()
        return [model for model in db_models]
