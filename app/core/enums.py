from enum import Enum, IntEnum
from typing import Optional
from uuid import UUID


class UserRoles(str, Enum):
    admin = "admin"
    user = "user"


class ModelStatus(str, Enum):
    pending = "pending"
    training = "training"
    completed = "completed"
    failed = "failed"


class TaskStatus(str, Enum):
    inference = "inference"
    training = "training"


class QueueTypes(str, Enum):
    inference_queue = "inference_queue"
    training_queue = "training_queue"


class ModelArchitectures(str, Enum):
    faster_rcnn = "faster_rcnn"
    yolo = "yolo"


class CacheTTL(IntEnum):
    DATASETS = 60 * 60
    MODELS = 120 * 60
    TASKS = 30 * 60
    USER = 30 * 60


class CacheKeysObject(str, Enum):
    DATASET = "dataset"
    MODEL = "model"
    TASK = "task"
    USER = "user"

    @staticmethod
    def dataset(dataset_id: UUID):
        return f"{CacheKeysObject.DATASET}:{dataset_id}"

    @staticmethod
    def model(model_id: UUID):
        return f"{CacheKeysObject.MODEL}:{model_id}"

    @staticmethod
    def task(task_id: UUID):
        return f"{CacheKeysObject.TASK}:{task_id}"

    @staticmethod
    def user(user_id: UUID):
        return f"{CacheKeysObject.USER}:{user_id}"


class CacheKeysList(str, Enum):
    DATASETS = "datasets"
    MODELS = "models"
    TASKS = "tasks"

    @staticmethod
    def datasets(user_id: UUID, skip: int = 0, limit: int = 100, name_contains: Optional[str] = None):
        name_contains_val = name_contains if name_contains else ""

        return f"{CacheKeysList.DATASETS}:{user_id}:{skip}:{limit}:{name_contains_val}"

    @staticmethod
    def models(user_id: UUID, skip: int = 0, limit: int = 100, status: Optional[str] = None,
               dataset_id: Optional[UUID] = None) -> str:
        s_val = status if status else "any"
        d_val = str(dataset_id) if dataset_id else "all"
        return f"{CacheKeysList.MODELS}:{user_id}:{skip}:{limit}:{s_val}:{d_val}"

    @staticmethod
    def tasks(user_id: UUID):
        return f"{CacheKeysList.TASKS}:{user_id}"
