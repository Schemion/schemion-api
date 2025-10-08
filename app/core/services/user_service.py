from typing import Optional
from uuid import UUID

from app.core import entities
from app.presentation.schemas import UserCreate
from app.core.interfaces.user_interface import UserInterface


class UserService:
    def __init__(self, user_repo: UserInterface):
        self.user_repo = user_repo

    def create_user(self, user: UserCreate) -> entities.User:
        existing_user = self.user_repo.get_user_by_email(str(user.email))
        if existing_user:
            raise ValueError("Email already registered")

        return self.user_repo.create_user(user)

    def get_user_by_email(self, email: str) -> Optional[entities.User]:
        return self.user_repo.get_user_by_email(email)


    def get_user_by_id(self, user_id: UUID) -> Optional[entities.User]:
        return self.user_repo.get_user_by_id(user_id)