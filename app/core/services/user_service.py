from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import entities
from app.core.enums import CacheKeysObject
from app.core.interfaces import ICacheRepository
from app.presentation.schemas import UserCreate
from app.core.interfaces.user_interface import IUserRepository


class UserService:
    def __init__(
            self,
            user_repo: IUserRepository,
            cache_repo: ICacheRepository
    ):
        self.user_repo = user_repo
        self.cache_repo = cache_repo

    async def create_user(self, session: AsyncSession, user: UserCreate) -> entities.User:
        existing_user = await self.user_repo.get_user_by_email(session,str(user.email))
        if existing_user:
            raise ValueError("Email already registered")

        created_user = await self.user_repo.create_user(session, user)

        await self.cache_repo.delete(CacheKeysObject.user(user_id = created_user.id))

        return created_user

    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[entities.User]:
        return await self.user_repo.get_user_by_email(session, email)


    async def get_user_by_id(self, session: AsyncSession, user_id: UUID) -> Optional[entities.User]:
        return await self.user_repo.get_user_by_id(session, user_id)

    async def get_user_datasets(self, session: AsyncSession, user_id: UUID) -> List[entities.Dataset]:
        return await self.user_repo.get_user_datasets(session, user_id)

    async def get_user_models(self, session: AsyncSession, user_id: UUID) -> List[entities.Model]:
        return await self.user_repo.get_user_models(session, user_id)