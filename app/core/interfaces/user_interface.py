from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import entities
from app.presentation import schemas


class IUserRepository(ABC):
    @abstractmethod
    async def create_user(self, db: AsyncSession, user: schemas.UserCreate) -> entities.User:
        ...

    @abstractmethod
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[entities.User]:
        ...

    @abstractmethod
    async def get_user_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[entities.User]:
        ...

    @abstractmethod
    async def get_user_datasets(self, db: AsyncSession, user_id: UUID) -> List[entities.Dataset]:
        ...

    @abstractmethod
    async def get_user_models(self, db: AsyncSession, user_id: UUID) -> List[entities.Model]:
        ...