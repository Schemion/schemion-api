from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.services.auth_service import AuthService
from app.presentation.schemas import LoginRequest, UserCreate
from app.core.enums import UserRoles
from tests.utils import run


class _Role(SimpleNamespace):
    pass


class _Permission(SimpleNamespace):
    pass


def test_register_existing_email_raises():
    user_repo = SimpleNamespace(
        get_user_by_email=AsyncMock(return_value=SimpleNamespace(id=uuid4())),
        create_user=AsyncMock(),
    )

    service = AuthService(user_repo)

    with pytest.raises(ValidationError):
        run(service.register(UserCreate(email="user@example.com", password="pw")))


def test_register_hashes_password_and_creates_user(monkeypatch):
    async def _hash(pw):
        return "hashed-pw"

    monkeypatch.setattr("app.core.services.auth_service.get_password_hash_async", _hash)

    created_user = SimpleNamespace(id=uuid4(), email="user@example.com", role=UserRoles.user)
    user_repo = SimpleNamespace(
        get_user_by_email=AsyncMock(return_value=None),
        create_user=AsyncMock(return_value=created_user),
    )

    service = AuthService(user_repo)
    result = run(service.register(UserCreate(email="user@example.com", password="pw")))

    created_arg = user_repo.create_user.call_args.args[0]
    assert created_arg.password == "hashed-pw"
    assert result.email == "user@example.com"


def test_login_invalid_email_raises():
    user_repo = SimpleNamespace(get_user_by_email=AsyncMock(return_value=None))
    service = AuthService(user_repo)

    with pytest.raises(UnauthorizedError):
        run(service.login(LoginRequest(email="user@example.com", password="pw")))


def test_login_invalid_password_raises(monkeypatch):
    user = SimpleNamespace(
        id=uuid4(),
        email="user@example.com",
        hashed_password="hashed",
        roles=[],
    )
    user_repo = SimpleNamespace(get_user_by_email=AsyncMock(return_value=user))

    monkeypatch.setattr("app.core.services.auth_service.verify_password_async", lambda *_: False)

    service = AuthService(user_repo)
    with pytest.raises(UnauthorizedError):
        run(service.login(LoginRequest(email="user@example.com", password="pw")))


def test_login_success_returns_token(monkeypatch):
    role = _Role(name="admin", permissions=[_Permission(name="read"), _Permission(name="write")])
    user = SimpleNamespace(
        id=uuid4(),
        email="user@example.com",
        hashed_password="hashed",
        roles=[role],
    )
    user_repo = SimpleNamespace(get_user_by_email=AsyncMock(return_value=user))

    monkeypatch.setattr("app.core.services.auth_service.verify_password_async", lambda *_: True)
    monkeypatch.setattr("app.core.services.auth_service.create_access_token", lambda *_: "token")

    service = AuthService(user_repo)
    token = run(service.login(LoginRequest(email="user@example.com", password="pw")))

    assert token.access_token == "token"
