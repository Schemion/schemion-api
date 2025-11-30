from enum import Enum, IntEnum
from uuid import UUID


class UserRole(str, Enum):
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
    DATASETS = 60
    MODELS = 120
    TASKS = 30
    USER = 30

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
    def datasets(user_id: UUID):
        return f"{CacheKeysList.DATASETS}:{user_id}"

    @staticmethod
    def models(user_id: UUID):
        return f"{CacheKeysList.MODELS}:{user_id}"

    @staticmethod
    def tasks(user_id: UUID):
        return f"{CacheKeysList.TASKS}:{user_id}"


