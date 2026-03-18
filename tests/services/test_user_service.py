from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from app.core.enums import CacheKeysObject, UserRoles
from app.core.exceptions import ValidationError
from app.core.services.user_service import UserService
from app.presentation.schemas import UserCreate
from tests.utils import run


def test_create_user_existing_email_raises():
    user_repo = SimpleNamespace(get_user_by_email=AsyncMock(return_value=SimpleNamespace(id=uuid4())))
    cache_repo = SimpleNamespace(delete=AsyncMock())

    service = UserService(user_repo, cache_repo)

    with pytest.raises(ValidationError):
        run(service.create_user(UserCreate(email="user@example.com", password="pw")))


def test_create_user_deletes_cache_and_returns_user():
    created_user = SimpleNamespace(id=uuid4(), email="user@example.com", role=UserRoles.user)
    user_repo = SimpleNamespace(
        get_user_by_email=AsyncMock(return_value=None),
        create_user=AsyncMock(return_value=created_user),
    )
    cache_repo = SimpleNamespace(delete=AsyncMock())

    service = UserService(user_repo, cache_repo)
    result = run(service.create_user(UserCreate(email="user@example.com", password="pw")))

    cache_repo.delete.assert_awaited_once_with(CacheKeysObject.user(user_id=created_user.id))
    assert result == created_user


def test_getters_delegate_to_repo():
    user_id = uuid4()
    user_repo = SimpleNamespace(
        get_user_by_email=AsyncMock(return_value="email-user"),
        get_user_by_id=AsyncMock(return_value="id-user"),
        get_user_datasets=AsyncMock(return_value=["d1"]),
        get_user_models=AsyncMock(return_value=["m1"]),
    )
    cache_repo = SimpleNamespace(delete=AsyncMock())

    service = UserService(user_repo, cache_repo)

    assert run(service.get_user_by_email("user@example.com")) == "email-user"
    assert run(service.get_user_by_id(user_id)) == "id-user"
    assert run(service.get_user_datasets(user_id)) == ["d1"]
    assert run(service.get_user_models(user_id)) == ["m1"]
