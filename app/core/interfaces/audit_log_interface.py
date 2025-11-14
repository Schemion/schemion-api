from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core import entities
from app.presentation import schemas

class AuditLogInterface(ABC):
    @abstractmethod
    def create_audit_log(self, audit_log: schemas.AuditLogCreate) -> entities.AuditLog:
        ...

    @abstractmethod
    def get_audit_log_by_id(self, audit_log_id:int) -> Optional[entities.AuditLog]:
        ...

    @abstractmethod
    def get_audit_logs(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> list[entities.AuditLog]:
        ...

    @abstractmethod
    def delete_audit_log_by_id(self, audit_log_id:int):
        ...
