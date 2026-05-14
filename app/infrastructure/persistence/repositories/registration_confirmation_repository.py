from datetime import datetime
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.interfaces.registration_confirmation_interface import IRegistrationConfirmationRepository
from app.infrastructure.persistence.models import RegistrationConfirmation


class RegistrationConfirmationRepository(IRegistrationConfirmationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[RegistrationConfirmation]:
        result = await self.session.execute(
            select(RegistrationConfirmation).where(RegistrationConfirmation.email == email)
        )
        return result.scalar_one_or_none()

    async def upsert_confirmation(
            self,
            email: str,
            hashed_password: str,
            code_hash: str,
            expires_at: datetime,
    ) -> RegistrationConfirmation:
        confirmation = await self.get_by_email(email)

        if confirmation is None:
            confirmation = RegistrationConfirmation(email=email)
            self.session.add(confirmation)

        confirmation.hashed_password = hashed_password
        confirmation.code_hash = code_hash
        confirmation.expires_at = expires_at
        confirmation.attempts = 0

        await self.session.commit()
        await self.session.refresh(confirmation)
        return confirmation

    async def increment_attempts(self, email: str) -> int:
        confirmation = await self.get_by_email(email)
        if confirmation is None:
            return 0

        confirmation.attempts += 1
        await self.session.commit()
        await self.session.refresh(confirmation)
        return int(confirmation.attempts)

    async def delete_by_email(self, email: str) -> None:
        await self.session.execute(
            delete(RegistrationConfirmation).where(RegistrationConfirmation.email == email)
        )
        await self.session.commit()
