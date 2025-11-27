from abc import ABC, abstractmethod
from typing import Any, Optional


class ICacheRepository(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    def set(self, key: str, value: Any, expire: int | None = None) -> None:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...