import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Model:
    id: uuid.UUID
    name: str
    version: str
    architecture: str
    architecture_profile: str # для того чтобы указать resnet и тд
    minio_model_path: str
    status: str
    user_id: Optional[uuid.UUID] = None
    is_system: bool = False
    base_model_id: Optional[uuid.UUID] = None
    dataset_id: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))