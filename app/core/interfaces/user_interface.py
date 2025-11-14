from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.core import entities
from app.presentation import schemas


class IUserRepository(ABC):
    @abstractmethod
    def create_user(self, user: schemas.UserCreate) -> entities.User:
        ...

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[entities.User]:
        ...

    @abstractmethod
    def get_user_by_id(self, user_id: UUID) -> Optional[entities.User]:
        ...

    @abstractmethod
    def get_user_datasets(self, user_id: UUID) -> List[entities.Dataset]:
        ...

    @abstractmethod
    def get_user_models(self, user_id: UUID) -> List[entities.Model]:
        ...