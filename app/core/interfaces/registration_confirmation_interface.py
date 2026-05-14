from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from app.infrastructure.persistence.models import RegistrationConfirmation


class IRegistrationConfirmationRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[RegistrationConfirmation]:
        ...

    @abstractmethod
    async def upsert_confirmation(
            self,
            email: str,
            hashed_password: str,
            code_hash: str,
            expires_at: datetime,
    ) -> RegistrationConfirmation:
        ...

    @abstractmethod
    async def increment_attempts(self, email: str) -> int:
        ...

    @abstractmethod
    async def delete_by_email(self, email: str) -> None:
        ...
