import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Model:
    id: uuid.UUID
    name: str
    version: str
    dataset_id: Optional[uuid.UUID]
    minio_model_path: str
    status: str
    created_at: datetime = datetime.now(timezone.utc)