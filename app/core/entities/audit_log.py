import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AuditLog:
    id: int
    user_id: Optional[uuid.UUID] = None
    action: str  = "" # TODO: Надо придумать что с этим делать
    details: Optional[dict] = None
    created_at: datetime = datetime.now(timezone.utc)