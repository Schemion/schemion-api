from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.common.security.dependencies import require_roles
from app.core.entities import User
from app.core.services import AuditLogService
from app.dependencies import get_db
from app.infrastructure.database.repositories import AuditLogRepository
from app.presentation.schemas import AuditLogCreate, AuditLogRead

router = APIRouter(prefix="/audit-logs", tags=["audit"])

@router.post("/create", response_model=AuditLogRead, status_code=201)
def create_audit_log(log: AuditLogCreate, db: Session = Depends(get_db),_: User = Depends(require_roles(["admin"]))):
    service = AuditLogService(AuditLogRepository(db))
    return service.create_audit_log(log)

@router.get("/", response_model=list[AuditLogRead])
def get_audit_logs( skip: int = 0,limit: int = 100,user_id: Optional[UUID] = None, action: Optional[str] = None,
                    since: Optional[datetime] = None,
                    db: Session = Depends(get_db),_: User = Depends(require_roles(["admin"]))):
    service = AuditLogService(AuditLogRepository(db))
    return service.get_audit_logs(skip, limit, user_id, action, since)

@router.get("/{log_id}", response_model=AuditLogRead)
def get_audit_log(log_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(["admin"]))):
    service = AuditLogService(AuditLogRepository(db))
    log = service.get_audit_log_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log

@router.delete("/{log_id}", status_code=204)
def delete_audit_log(log_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles(["admin"]))):
    service = AuditLogService(AuditLogRepository(db))
    service.delete_audit_log_by_id(log_id)