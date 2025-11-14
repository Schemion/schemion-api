from enum import Enum


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