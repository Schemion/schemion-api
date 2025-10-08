import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class User:
    id: uuid.UUID
    email: str
    hashed_password: str
    role: str
    created_at: datetime = datetime.now(timezone.utc)