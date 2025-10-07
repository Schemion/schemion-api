import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    action: str
    details: Optional[Dict[str, Any]] = None


class AuditLogCreate(AuditLogBase):
    user_id: Optional[uuid.UUID] = None


class AuditLogRead(AuditLogBase):
    id: int
    user_id: Optional[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)
