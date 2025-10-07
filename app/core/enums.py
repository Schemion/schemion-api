from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    user = "user"


class ModelStatus(str, Enum):
    pending = "pending"
    training = "training"
    completed = "completed"
    failed = "failed"
