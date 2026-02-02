from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID


from app.infrastructure.database.models import Dataset, Model, User
from app.presentation import schemas


class IUserRepository(ABC):
    @abstractmethod
    async def create_user(self, user: schemas.UserCreate) -> User:
        ...

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        ...

    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        ...

    @abstractmethod
    async def get_user_datasets(self, user_id: UUID) -> List[Dataset]:
        ...

    @abstractmethod
    async def get_user_models(self, user_id: UUID) -> List[Model]:
        ...