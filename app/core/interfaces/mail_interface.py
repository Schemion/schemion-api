from abc import ABC, abstractmethod


class IMailService(ABC):
    @abstractmethod
    async def send_registration_confirmation(self, email: str, code: str) -> None:
        ...
