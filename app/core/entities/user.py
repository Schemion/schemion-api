import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class User:
    id: uuid.UUID
    email: str
    hashed_password: str
    role: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class UserLight:
    id: uuid.UUID
    email: str
    role: str