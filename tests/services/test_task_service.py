from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.enums import CacheKeysList, CacheKeysObject
from app.core.exceptions import ValidationError
from app.core.services.task_service import TaskService
from app.presentation.schemas import TaskCreate
from tests.utils import run


def test_create_inference_task_invalid_content_type():
    task_repo = SimpleNamespace(create_inference_task=AsyncMock())
    storage = SimpleNamespace(upload_file=AsyncMock())
    model_repo = SimpleNamespace(get_model_by_id=AsyncMock(return_value=SimpleNamespace(id=uuid4())))
    dataset_repo = SimpleNamespace()
    cache_repo = SimpleNamespace(delete=AsyncMock())

    service = TaskService(task_repo, storage, model_repo, dataset_repo, cache_repo)
    task = TaskCreate(task_type="inference", user_id=uuid4(), model_id=uuid4())

    with pytest.raises(ValidationError):
        run(service.create_inference_task(task, b"data", "file.txt", "text/plain", task.user_id))


def test_create_inference_task_uploads_and_publishes(monkeypatch):
    send_task = MagicMock()
    monkeypatch.setattr("app.core.services.task_service.celery_app", SimpleNamespace(send_task=send_task))

    user_id = uuid4()
    model_id = uuid4()
    task_repo = SimpleNamespace(create_inference_task=AsyncMock(return_value=SimpleNamespace(id=uuid4(), user_id=user_id)))
    storage = SimpleNamespace(upload_file=AsyncMock(return_value="input"))
    model_repo = SimpleNamespace(get_model_by_id=AsyncMock(return_value=SimpleNamespace(id=model_id, architecture="arch")))
    dataset_repo = SimpleNamespace()
    cache_repo = SimpleNamespace(delete=AsyncMock())

    service = TaskService(task_repo, storage, model_repo, dataset_repo, cache_repo)
    task = TaskCreate(task_type="inference", user_id=user_id, model_id=model_id)

    result = run(service.create_inference_task(task, b"data", "file.jpg", "image/jpeg", user_id))

    assert result.user_id == user_id
    send_task.assert_called_once()
    cache_repo.delete.assert_any_await(CacheKeysObject.task(task_id=result.id))
    cache_repo.delete.assert_any_await(CacheKeysList.tasks(user_id=user_id))


def test_create_training_task_publishes_and_clears_cache(monkeypatch):
    send_task = MagicMock()
    monkeypatch.setattr("app.core.services.task_service.celery_app", SimpleNamespace(send_task=send_task))

    task_repo = SimpleNamespace(create_training_task=AsyncMock(return_value=SimpleNamespace(id=uuid4())))
    storage = SimpleNamespace()
    model_repo = SimpleNamespace()
    dataset_repo = SimpleNamespace(get_dataset_by_id=AsyncMock(return_value=SimpleNamespace(id=uuid4())))
    cache_repo = SimpleNamespace(delete=AsyncMock())

    service = TaskService(task_repo, storage, model_repo, dataset_repo, cache_repo)
    task = TaskCreate(task_type="training", user_id=uuid4(), model_id=uuid4(), dataset_id=uuid4())

    result = run(service.create_training_task(task))

    assert result.id is not None
    send_task.assert_called_once()
    cache_repo.delete.assert_awaited_once_with(CacheKeysObject.task(task_id=result.id))


def test_get_task_by_id_uses_cache():
    task_id = uuid4()
    user_id = uuid4()
    cached = {"id": task_id, "user_id": user_id, "task_type": "inference"}

    task_repo = SimpleNamespace(get_task_by_id=AsyncMock())
    storage = SimpleNamespace(get_presigned_file_url=AsyncMock())
    model_repo = SimpleNamespace()
    dataset_repo = SimpleNamespace()
    cache_repo = SimpleNamespace(get=AsyncMock(return_value=cached), set=AsyncMock())

    service = TaskService(task_repo, storage, model_repo, dataset_repo, cache_repo)
    result = run(service.get_task_by_id(task_id, user_id))

    assert result.id == task_id
    task_repo.get_task_by_id.assert_not_called()


def test_get_task_by_id_attaches_output_url():
    task_id = uuid4()
    user_id = uuid4()
    task = SimpleNamespace(id=task_id, user_id=user_id, task_type="inference", output_path="out")

    task_repo = SimpleNamespace(get_task_by_id=AsyncMock(return_value=task))
    storage = SimpleNamespace(get_presigned_file_url=AsyncMock(return_value="url"))
    model_repo = SimpleNamespace()
    dataset_repo = SimpleNamespace()
    cache_repo = SimpleNamespace(get=AsyncMock(return_value=None), set=AsyncMock())

    service = TaskService(task_repo, storage, model_repo, dataset_repo, cache_repo)
    result = run(service.get_task_by_id(task_id, user_id))

    assert result.output_url == "url"
