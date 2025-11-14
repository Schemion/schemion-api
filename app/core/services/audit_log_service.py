from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core import entities
from app.core.interfaces import AuditLogInterface
from app.presentation.schemas import AuditLogCreate


class AuditLogService:
    def __init__(self, audit_log_repo: AuditLogInterface):
        self.audit_log_repo = audit_log_repo

    def create_audit_log(self,  audit_log: AuditLogCreate) -> entities.AuditLog:
        return self.audit_log_repo.create_audit_log(audit_log)

    def get_audit_log_by_id(self, audit_log_id: int):
        return self.audit_log_repo.get_audit_log_by_id(audit_log_id)

    def get_audit_logs(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None, action: Optional[str] = None, since: Optional[datetime] = None) -> list[entities.AuditLog]:
        return self.audit_log_repo.get_audit_logs(skip, limit, user_id, action, since)

    def delete_audit_log_by_id(self, audit_log_id: int) -> None:
        self.audit_log_repo.delete_audit_log_by_id(audit_log_id)