import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Task:
    id: uuid.UUID
    user_id: uuid.UUID
    task_type: str
    model_id: uuid.UUID
    dataset_id: Optional[uuid.UUID] = None
    input_path: Optional[str] = None
    output_path: Optional[str] = None
    error_msg: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)