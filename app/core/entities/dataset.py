import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Dataset:
    id: uuid.UUID
    name: str
    minio_path: str
    description: Optional[str] = None
    num_samples: int = 0
    created_at: datetime = datetime.now(timezone.utc)