from typing import Optional, List
from uuid import UUID
from app.core import entities
from app.presentation.schemas import UserCreate
from app.core.interfaces.user_interface import IUserRepository


class UserService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def create_user(self, user: UserCreate) -> entities.User:
        existing_user = await self.user_repo.get_user_by_email(str(user.email))
        if existing_user:
            raise ValueError("Email already registered")

        return await self.user_repo.create_user(user)

    async def get_user_by_email(self, email: str) -> Optional[entities.User]:
        return await self.user_repo.get_user_by_email(email)


    async def get_user_by_id(self, user_id: UUID) -> Optional[entities.User]:
        return await self.user_repo.get_user_by_id(user_id)

    async def get_user_datasets(self, user_id: UUID) -> List[entities.Dataset]:
        return await self.user_repo.get_user_datasets(user_id)

    async def get_user_models(self, user_id: UUID) -> List[entities.Model]:
        return await self.user_repo.get_user_models(user_id)