from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from app.core.enums import CacheKeysList, CacheKeysObject
from app.core.services.dataset_service import DatasetService
from app.presentation.schemas import DatasetCreate
from tests.utils import run


def test_create_dataset_uploads_and_clears_cache(monkeypatch):
    monkeypatch.setattr("app.core.services.dataset_service.validate_dataset_archive", lambda *_: None)

    user_id = uuid4()
    dataset = DatasetCreate(name="ds")
    created = SimpleNamespace(id=uuid4(), user_id=user_id, name="ds", minio_path="obj")

    dataset_repo = SimpleNamespace(create_dataset=AsyncMock(return_value=created))
    storage = SimpleNamespace(upload_file=AsyncMock(return_value="obj"))
    cache_repo = SimpleNamespace(delete=AsyncMock(), delete_pattern=AsyncMock())

    service = DatasetService(dataset_repo, storage, cache_repo)
    result = run(service.create_dataset(dataset, b"data", "file.zip", "application/zip", user_id))

    assert dataset.minio_path == "obj"
    dataset_repo.create_dataset.assert_awaited_once()
    cache_repo.delete.assert_awaited_once_with(CacheKeysObject.dataset(dataset_id=created.id))
    cache_repo.delete_pattern.assert_awaited_once_with(f"{CacheKeysList.DATASETS}:{user_id}:*")
    assert result == created


def test_get_dataset_by_id_uses_cache():
    user_id = uuid4()
    dataset_id = uuid4()
    cached = {"id": dataset_id, "user_id": user_id, "name": "ds", "minio_path": "obj"}

    dataset_repo = SimpleNamespace(get_dataset_by_id=AsyncMock())
    storage = SimpleNamespace()
    cache_repo = SimpleNamespace(get=AsyncMock(return_value=cached), set=AsyncMock())

    service = DatasetService(dataset_repo, storage, cache_repo)
    result = run(service.get_dataset_by_id(dataset_id, user_id))

    assert result.id == dataset_id
    dataset_repo.get_dataset_by_id.assert_not_called()


def test_get_dataset_by_id_permission_denied():
    user_id = uuid4()
    dataset_id = uuid4()
    dataset = SimpleNamespace(id=dataset_id, user_id=uuid4(), name="ds", minio_path="obj")

    dataset_repo = SimpleNamespace(get_dataset_by_id=AsyncMock(return_value=dataset))
    storage = SimpleNamespace()
    cache_repo = SimpleNamespace(get=AsyncMock(return_value=None), set=AsyncMock())

    service = DatasetService(dataset_repo, storage, cache_repo)

    with pytest.raises(PermissionError):
        run(service.get_dataset_by_id(dataset_id, user_id))


def test_delete_dataset_by_id_deletes_storage_and_cache():
    user_id = uuid4()
    dataset_id = uuid4()
    dataset = SimpleNamespace(id=dataset_id, user_id=user_id, minio_path="obj")

    dataset_repo = SimpleNamespace(
        get_dataset_by_id=AsyncMock(return_value=dataset),
        delete_dataset_by_id=AsyncMock(),
    )
    storage = SimpleNamespace(delete_file=AsyncMock())
    cache_repo = SimpleNamespace(delete=AsyncMock(), delete_pattern=AsyncMock())

    service = DatasetService(dataset_repo, storage, cache_repo)
    run(service.delete_dataset_by_id(dataset_id, user_id))

    storage.delete_file.assert_awaited_once()
    dataset_repo.delete_dataset_by_id.assert_awaited_once_with(dataset_id)
    cache_repo.delete.assert_awaited_once_with(CacheKeysObject.dataset(dataset_id=dataset_id))
    cache_repo.delete_pattern.assert_awaited_once_with(f"{CacheKeysList.DATASETS}:{user_id}:*")


def test_download_dataset_checks_access_and_returns_url():
    user_id = uuid4()
    dataset_id = uuid4()
    dataset = SimpleNamespace(id=dataset_id, user_id=user_id, minio_path="obj")

    dataset_repo = SimpleNamespace(get_dataset_by_id=AsyncMock(return_value=dataset))
    storage = SimpleNamespace(get_presigned_file_url=AsyncMock(return_value="url"))
    cache_repo = SimpleNamespace(get=AsyncMock(return_value=None))

    service = DatasetService(dataset_repo, storage, cache_repo)
    url = run(service.download_dataset(dataset_id, user_id))

    assert url == "url"
