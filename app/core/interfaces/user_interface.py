from typing import Protocol, Optional
from uuid import UUID

from app.core import entities
from app.presentation import schemas


class UserInterface(Protocol):
    def create_user(self, user: schemas.UserCreate) -> entities.User:
        ...

    def get_user_by_email(self, email: str) -> Optional[entities.User]:
        ...

    def get_user_by_id(self, user_id: UUID) -> Optional[entities.User]:
        ...
