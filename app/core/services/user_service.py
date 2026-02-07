from typing import List, Optional
from uuid import UUID

from app.core.enums import CacheKeysObject
from app.core.exceptions import ValidationError
from app.core.interfaces import ICacheRepository
from app.core.interfaces.user_interface import IUserRepository
from app.presentation.schemas import DatasetRead, ModelRead, UserCreate, UserRead


class UserService:
    def __init__(
            self,
            user_repo: IUserRepository,
            cache_repo: ICacheRepository
    ):
        self.user_repo = user_repo
        self.cache_repo = cache_repo

    async def create_user(self, user: UserCreate) -> UserRead:
        existing_user = await self.user_repo.get_user_by_email(str(user.email))
        if existing_user:
            raise ValidationError("Email already registered")

        created_user = await self.user_repo.create_user(user)

        await self.cache_repo.delete(CacheKeysObject.user(user_id=created_user.id))

        return created_user

    async def get_user_by_email(self, email: str) -> Optional[UserRead]:
        return await self.user_repo.get_user_by_email(email)

    async def get_user_by_id(self, user_id: UUID) -> Optional[UserRead]:
        return await self.user_repo.get_user_by_id(user_id)

    async def get_user_datasets(self, user_id: UUID) -> List[DatasetRead]:
        return await self.user_repo.get_user_datasets(user_id)

    async def get_user_models(self, user_id: UUID) -> List[ModelRead]:
        return await self.user_repo.get_user_models(user_id)
