from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from app.core.enums import CacheKeysList, CacheKeysObject
from app.core.services.model_service import ModelService
from app.presentation.schemas import ModelCreate
from tests.utils import run


def test_create_model_uploads_and_clears_cache(monkeypatch):
    async def _validate(*_):
        return None

    monkeypatch.setattr("app.core.services.model_service.validate_model_file", _validate)

    user_id = uuid4()
    model = ModelCreate(name="m", architecture="arch", architecture_profile="p")
    created = SimpleNamespace(id=uuid4(), user_id=user_id, is_system=False, minio_model_path="obj")

    model_repo = SimpleNamespace(create_model=AsyncMock(return_value=created))
    dataset_repo = SimpleNamespace(get_dataset_by_id=AsyncMock())
    storage = SimpleNamespace(upload_file=AsyncMock(return_value="obj"))
    cache_repo = SimpleNamespace(delete=AsyncMock(), delete_pattern=AsyncMock())

    service = ModelService(model_repo, storage, dataset_repo, cache_repo)
    result = run(service.create_model(model, b"data", "model.pt", "application/octet-stream", user_id))

    assert model.minio_model_path == "obj"
    cache_repo.delete.assert_awaited_once_with(CacheKeysObject.model(model_id=created.id))
    cache_repo.delete_pattern.assert_awaited_once_with(f"{CacheKeysList.MODELS}:{user_id}:*")
    assert result == created


def test_get_model_by_id_uses_cache():
    user_id = uuid4()
    model_id = uuid4()
    cached = {
        "id": model_id,
        "user_id": user_id,
        "name": "m",
        "architecture": "a",
        "architecture_profile": "p",
        "is_system": False,
        "minio_model_path": "obj",
        "dataset_id": None,
        "base_model_id": None,
    }

    model_repo = SimpleNamespace(get_model_by_id=AsyncMock())
    dataset_repo = SimpleNamespace()
    storage = SimpleNamespace()
    cache_repo = SimpleNamespace(get=AsyncMock(return_value=cached), set=AsyncMock())

    service = ModelService(model_repo, storage, dataset_repo, cache_repo)
    result = run(service.get_model_by_id(model_id, user_id))

    assert result.id == model_id
    model_repo.get_model_by_id.assert_not_called()


def test_delete_model_by_id_rejects_system_model():
    user_id = uuid4()
    model_id = uuid4()
    model = SimpleNamespace(id=model_id, user_id=user_id, is_system=True)

    model_repo = SimpleNamespace(get_model_by_id=AsyncMock(return_value=model))
    dataset_repo = SimpleNamespace()
    storage = SimpleNamespace(delete_file=AsyncMock())
    cache_repo = SimpleNamespace(delete=AsyncMock(), delete_pattern=AsyncMock())

    service = ModelService(model_repo, storage, dataset_repo, cache_repo)

    with pytest.raises(PermissionError):
        run(service.delete_model_by_id(model_id, user_id))


def test_download_model_returns_url():
    user_id = uuid4()
    model_id = uuid4()
    model = SimpleNamespace(id=model_id, user_id=user_id, is_system=False, minio_model_path="obj")

    model_repo = SimpleNamespace(get_model_by_id=AsyncMock(return_value=model))
    dataset_repo = SimpleNamespace()
    storage = SimpleNamespace(get_presigned_file_url=AsyncMock(return_value="url"))
    cache_repo = SimpleNamespace()

    service = ModelService(model_repo, storage, dataset_repo, cache_repo)
    url = run(service.download_model(model_id, user_id))

    assert url == "url"
