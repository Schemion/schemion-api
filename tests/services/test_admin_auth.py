from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from app.common.admin.admin import AdminAuth
from tests.utils import run


class _ContainerContext:
    def __init__(self, user_service):
        self._user_service = user_service

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, _cls):
        return self._user_service


class _DishkaContainer:
    def __init__(self, user_service):
        self._user_service = user_service

    def __call__(self):
        return _ContainerContext(self._user_service)


def _make_request(user_service, username: str, password: str, session: dict | None = None):
    async def _form():
        return {"username": username, "password": password}

    return SimpleNamespace(
        form=_form,
        session=session if session is not None else {},
        app=SimpleNamespace(
            state=SimpleNamespace(dishka_container=_DishkaContainer(user_service)),
        ),
    )


def test_admin_login_success_sets_session_token(monkeypatch):
    user = SimpleNamespace(
        id=uuid4(),
        hashed_password="hashed",
        roles=[SimpleNamespace(name="admin")],
    )
    user_service = SimpleNamespace(
        get_user_by_email=AsyncMock(return_value=user),
        get_user_by_id=AsyncMock(return_value=user),
    )
    request = _make_request(user_service, username="admin@schemion.local", password="pw")

    async def _verify_password(*_args, **_kwargs):
        return True

    monkeypatch.setattr("app.common.admin.admin.verify_password_async", _verify_password)

    auth = AdminAuth()
    assert run(auth.login(request)) is True
    assert isinstance(request.session.get("token"), str)


def test_admin_login_rejects_non_admin(monkeypatch):
    user = SimpleNamespace(
        id=uuid4(),
        hashed_password="hashed",
        roles=[SimpleNamespace(name="user")],
    )
    user_service = SimpleNamespace(
        get_user_by_email=AsyncMock(return_value=user),
        get_user_by_id=AsyncMock(return_value=user),
    )
    request = _make_request(user_service, username="user@schemion.local", password="pw")

    async def _verify_password(*_args, **_kwargs):
        return True

    monkeypatch.setattr("app.common.admin.admin.verify_password_async", _verify_password)

    auth = AdminAuth()
    assert run(auth.login(request)) is False
    assert request.session.get("token") is None


def test_admin_authenticate_success_for_admin(monkeypatch):
    user_id = uuid4()
    user = SimpleNamespace(
        id=user_id,
        hashed_password="hashed",
        roles=[SimpleNamespace(name="admin")],
    )
    user_service = SimpleNamespace(
        get_user_by_email=AsyncMock(return_value=user),
        get_user_by_id=AsyncMock(return_value=user),
    )
    request = _make_request(
        user_service,
        username="admin@schemion.local",
        password="pw",
        session={"token": "session-token"},
    )
    monkeypatch.setattr("app.common.admin.admin.jwt.decode", lambda *_args, **_kwargs: {"sub": str(user_id)})

    auth = AdminAuth()
    assert run(auth.authenticate(request)) is True


def test_admin_authenticate_rejects_non_admin(monkeypatch):
    user_id = uuid4()
    user = SimpleNamespace(
        id=user_id,
        hashed_password="hashed",
        roles=[SimpleNamespace(name="user")],
    )
    user_service = SimpleNamespace(
        get_user_by_email=AsyncMock(return_value=user),
        get_user_by_id=AsyncMock(return_value=user),
    )
    request = _make_request(
        user_service,
        username="user@schemion.local",
        password="pw",
        session={"token": "session-token"},
    )
    monkeypatch.setattr("app.common.admin.admin.jwt.decode", lambda *_args, **_kwargs: {"sub": str(user_id)})

    auth = AdminAuth()
    assert run(auth.authenticate(request)) is False
