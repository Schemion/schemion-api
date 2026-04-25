from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from app.core.enums import CacheKeysList, CacheKeysObject, QueueTypes, TaskType
from app.core.exceptions import NotFoundError, ValidationError
from app.core.services.task_service import TaskService
from app.presentation.schemas import TaskCreate
from tests.utils import run


class _FakeBobberPublisher:
    def __init__(self, inference_ok: bool = True, training_ok: bool = True):
        self.inference_ok = inference_ok
        self.training_ok = training_ok
        self.inference_calls = []
        self.training_calls = []

    def publish_inference(self, queue, message):
        self.inference_calls.append((queue, message))
        return self.inference_ok

    def publish_training(self, queue, message):
        self.training_calls.append((queue, message))
        return self.training_ok


def test_create_inference_task_without_model_id_raises_not_found():
    task_repo = SimpleNamespace(create_inference_task=AsyncMock())
    storage = SimpleNamespace(upload_file=AsyncMock())
    model_repo = SimpleNamespace(get_model_by_id=AsyncMock())
    dataset_repo = SimpleNamespace()
    cache_repo = SimpleNamespace(delete=AsyncMock(), delete_pattern=AsyncMock())

    service = TaskService(task_repo, storage, model_repo, dataset_repo, cache_repo, _FakeBobberPublisher())
    task = TaskCreate(task_type=TaskType.inference, user_id=uuid4(), model_id=None)

    with pytest.raises(NotFoundError):
        run(service.create_inference_task(task, b"data", "file.jpg", "image/jpeg", task.user_id))


def test_create_inference_task_invalid_content_type():
    model_id = uuid4()
    task_repo = SimpleNamespace(create_inference_task=AsyncMock())
    storage = SimpleNamespace(upload_file=AsyncMock())
    model_repo = SimpleNamespace(get_model_by_id=AsyncMock(return_value=SimpleNamespace(id=model_id)))
    dataset_repo = SimpleNamespace()
    cache_repo = SimpleNamespace(delete=AsyncMock(), delete_pattern=AsyncMock())

    service = TaskService(task_repo, storage, model_repo, dataset_repo, cache_repo, _FakeBobberPublisher())
    task = TaskCreate(task_type=TaskType.inference, user_id=uuid4(), model_id=model_id)

    with pytest.raises(ValidationError):
        run(service.create_inference_task(task, b"data", "file.txt", "text/plain", task.user_id))


def test_create_inference_task_uploads_publishes_and_clears_cache():
    user_id = uuid4()
    model_id = uuid4()
    created = SimpleNamespace(id=uuid4(), user_id=user_id)
    model = SimpleNamespace(id=model_id, architecture="yolo")

    task_repo = SimpleNamespace(create_inference_task=AsyncMock(return_value=created))
    storage = SimpleNamespace(upload_file=AsyncMock(return_value="input/path"))
    model_repo = SimpleNamespace(get_model_by_id=AsyncMock(return_value=model))
    dataset_repo = SimpleNamespace()
    cache_repo = SimpleNamespace(delete=AsyncMock(), delete_pattern=AsyncMock())
    bobber = _FakeBobberPublisher()

    service = TaskService(task_repo, storage, model_repo, dataset_repo, cache_repo, bobber)
    task = TaskCreate(task_type=TaskType.inference, user_id=user_id, model_id=model_id)

    result = run(service.create_inference_task(task, b"data", "file.jpg", "image/jpeg", user_id))

    assert result == created
    assert len(bobber.inference_calls) == 1
    queue, message = bobber.inference_calls[0]
    assert queue == QueueTypes.inference_queue
    assert message["task_id"] == str(created.id)
    assert message["task_type"] == TaskType.inference
    assert message["model_id"] == str(model_id)
    assert message["model_arch"] == "yolo"
    assert message["input_path"] == "input/path"

    cache_repo.delete.assert_awaited_once_with(CacheKeysObject.task(task_id=created.id))
    cache_repo.delete_pattern.assert_awaited_once_with(f"{CacheKeysList.TASKS}:{user_id}:*")


def test_create_training_task_publishes_and_clears_cache():
    user_id = uuid4()
    model_id = uuid4()
    dataset_id = uuid4()
    created = SimpleNamespace(id=uuid4(), user_id=user_id)

    task_repo = SimpleNamespace(create_training_task=AsyncMock(return_value=created))
    storage = SimpleNamespace()
    model_repo = SimpleNamespace()
    dataset_repo = SimpleNamespace(get_dataset_by_id=AsyncMock(return_value=SimpleNamespace(id=dataset_id)))
    cache_repo = SimpleNamespace(delete=AsyncMock(), delete_pattern=AsyncMock())
    bobber = _FakeBobberPublisher()

    service = TaskService(task_repo, storage, model_repo, dataset_repo, cache_repo, bobber)
    task = TaskCreate(
        task_type=TaskType.training,
        user_id=user_id,
        model_id=model_id,
        dataset_id=dataset_id,
        image_size=640,
        epochs=10,
        name="train-v1",
    )

    result = run(service.create_training_task(task))

    assert result == created
    assert len(bobber.training_calls) == 1
    queue, message = bobber.training_calls[0]
    assert queue == QueueTypes.training_queue
    assert message["task_id"] == str(created.id)
    assert message["task_type"] == TaskType.training
    assert message["model_id"] == str(model_id)
    assert message["dataset_id"] == str(dataset_id)
    assert message["image_size"] == 640
    assert message["epochs"] == 10
    assert message["name"] == "train-v1"

    cache_repo.delete.assert_awaited_once_with(CacheKeysObject.task(task_id=created.id))
    cache_repo.delete_pattern.assert_awaited_once_with(f"{CacheKeysList.TASKS}:{user_id}:*")


def test_get_task_by_id_uses_cache():
    task_id = uuid4()
    user_id = uuid4()
    cached = {"id": task_id, "user_id": user_id, "task_type": TaskType.inference, "status": "queued"}

    task_repo = SimpleNamespace(get_task_by_id=AsyncMock())
    storage = SimpleNamespace(get_presigned_file_url=AsyncMock())
    model_repo = SimpleNamespace()
    dataset_repo = SimpleNamespace()
    cache_repo = SimpleNamespace(get=AsyncMock(return_value=cached), set=AsyncMock())

    service = TaskService(task_repo, storage, model_repo, dataset_repo, cache_repo, _FakeBobberPublisher())
    result = run(service.get_task_by_id(task_id, user_id))

    assert result.id == task_id
    task_repo.get_task_by_id.assert_not_called()


def test_get_task_by_id_attaches_output_url_and_writes_cache():
    task_id = uuid4()
    user_id = uuid4()
    task = SimpleNamespace(id=task_id, user_id=user_id, task_type=TaskType.inference, output_path="out")

    task_repo = SimpleNamespace(get_task_by_id=AsyncMock(return_value=task))
    storage = SimpleNamespace(get_presigned_file_url=AsyncMock(return_value="url"))
    model_repo = SimpleNamespace()
    dataset_repo = SimpleNamespace()
    cache_repo = SimpleNamespace(get=AsyncMock(return_value=None), set=AsyncMock())

    service = TaskService(task_repo, storage, model_repo, dataset_repo, cache_repo, _FakeBobberPublisher())
    result = run(service.get_task_by_id(task_id, user_id))

    assert result.output_url == "url"
    cache_repo.set.assert_awaited_once()


def test_delete_task_by_id_clears_task_and_list_cache_patterns():
    task_id = uuid4()
    user_id = uuid4()
    task = SimpleNamespace(id=task_id, user_id=user_id)

    task_repo = SimpleNamespace(
        get_task_by_id=AsyncMock(return_value=task),
        delete_task_by_id=AsyncMock(),
    )
    storage = SimpleNamespace()
    model_repo = SimpleNamespace()
    dataset_repo = SimpleNamespace()
    cache_repo = SimpleNamespace(get=AsyncMock(), delete_pattern=AsyncMock())

    service = TaskService(task_repo, storage, model_repo, dataset_repo, cache_repo, _FakeBobberPublisher())
    run(service.delete_task_by_id(task_id, user_id))

    task_repo.delete_task_by_id.assert_awaited_once_with(task_id)
    cache_repo.delete_pattern.assert_any_await(CacheKeysObject.task(task_id=task_id))
    cache_repo.delete_pattern.assert_any_await(f"{CacheKeysList.TASKS}:{user_id}:*")
