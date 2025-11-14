from datetime import datetime
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session
from typing import Optional

from app.core.interfaces import AuditLogInterface
from app.infrastructure.database import models
from app.presentation import schemas
from app.core.entities.audit_log import AuditLog as EntityAuditLog


class AuditLogRepository(AuditLogInterface):
    def __init__(self, db: Session):
        self.db = db

    def create_audit_log(self, audit_log: schemas.AuditLogCreate) -> EntityAuditLog:
        db_log = models.AuditLog(
            user_id=audit_log.user_id,
            action=audit_log.action,
            details=audit_log.details,
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return self._to_entity(db_log)

    def get_audit_log_by_id(self, audit_log_id: int) -> Optional[EntityAuditLog]:
        db_log = self.db.query(models.AuditLog).filter(audit_log_id == models.AuditLog.id).first()
        return self._to_entity(db_log) if db_log else None

    def get_audit_logs(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None, action: Optional[str] = None, since: Optional[datetime] = None) -> list[EntityAuditLog]:
        query = self.db.query(models.AuditLog)

        filters = []
        if user_id is not None:
            filters.append(models.AuditLog.user_id == user_id)
        if action is not None:
            filters.append(models.AuditLog.action == action)
        if since is not None:
            filters.append(models.AuditLog.created_at >= since)

        if filters:
            query = query.filter(and_(*filters))

        db_logs = query.order_by(models.AuditLog.created_at.desc()).offset(skip).limit(limit).all()
        return [self._to_entity(log) for log in db_logs]

    def delete_audit_log_by_id(self, audit_log_id: int) -> None:
        db_log = self.db.query(models.AuditLog).filter(audit_log_id == models.AuditLog.id).first()
        if db_log:
            self.db.delete(db_log)
            self.db.commit()

    @staticmethod
    def _to_entity(db_log: models.AuditLog) -> EntityAuditLog:
        return EntityAuditLog(
            id=db_log.id,
            user_id=db_log.user_id,
            action=db_log.action,
            details=db_log.details,
            created_at=db_log.created_at,
        )

    @staticmethod
    def _to_orm(entity: EntityAuditLog) -> models.AuditLog:
        return EntityAuditLog(
            id=entity.id,
            user_id=entity.user_id,
            action=entity.action,
            details=entity.details,
            created_at=entity.created_at,
        )