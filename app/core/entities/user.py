import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Set


@dataclass
class User:
    id: uuid.UUID
    email: str
    hashed_password: str
    roles: Set[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class UserLight:
    id: uuid.UUID
    email: str
    roles: Set[str]