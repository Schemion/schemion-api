from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.enums import UserRoles
from app.core.exceptions import MailDeliveryError, ServiceUnavailableError, UnauthorizedError, ValidationError
from app.core.services.auth_service import AuthService
from app.presentation.schemas import LoginRequest, RefreshTokenRequest, RegistrationConfirmRequest, UserCreate
from tests.utils import run


class _Role(SimpleNamespace):
    pass


class _Permission(SimpleNamespace):
    pass


def _make_service(user_repo, confirmation_repo=None, mail_service=None):
    confirmation_repo = confirmation_repo or SimpleNamespace(
        get_by_email=AsyncMock(),
        upsert_confirmation=AsyncMock(),
        increment_attempts=AsyncMock(),
        delete_by_email=AsyncMock(),
    )
    mail_service = mail_service or SimpleNamespace(send_registration_confirmation=AsyncMock())
    return AuthService(user_repo, confirmation_repo, mail_service)


def test_register_existing_email_raises():
    user_repo = SimpleNamespace(get_user_by_email=AsyncMock(return_value=SimpleNamespace(id=uuid4())))
    service = _make_service(user_repo)

    with pytest.raises(ValidationError):
        run(service.register(UserCreate(email="user@example.com", password="pw")))


def test_register_hashes_password_stores_confirmation_and_sends_code(monkeypatch):
    async def _hash(pw):
        return "hashed-pw"

    monkeypatch.setattr("app.core.services.auth_service.get_password_hash_async", _hash)
    monkeypatch.setattr(AuthService, "_generate_confirmation_code", lambda *_: "123456")
    monkeypatch.setattr(AuthService, "_hash_confirmation_code", lambda *args: "code-hash")
    monkeypatch.setattr(AuthService, "_confirmation_expires_at", lambda *_: "expires-at")

    user_repo = SimpleNamespace(get_user_by_email=AsyncMock(return_value=None))
    confirmation_repo = SimpleNamespace(
        upsert_confirmation=AsyncMock(),
        delete_by_email=AsyncMock(),
    )
    mail_service = SimpleNamespace(send_registration_confirmation=AsyncMock())

    service = _make_service(user_repo, confirmation_repo, mail_service)
    result = run(service.register(UserCreate(email="user@example.com", password="pw")))

    confirmation_repo.upsert_confirmation.assert_awaited_once_with(
        email="user@example.com",
        hashed_password="hashed-pw",
        code_hash="code-hash",
        expires_at="expires-at",
    )
    mail_service.send_registration_confirmation.assert_awaited_once_with("user@example.com", "123456")
    assert result.detail == "Registration confirmation code sent"


def test_register_deletes_confirmation_when_mail_delivery_fails(monkeypatch):
    async def _hash(pw):
        return "hashed-pw"

    async def _send(*_):
        raise MailDeliveryError("smtp down")

    monkeypatch.setattr("app.core.services.auth_service.get_password_hash_async", _hash)
    monkeypatch.setattr(AuthService, "_generate_confirmation_code", lambda *_: "123456")
    monkeypatch.setattr(AuthService, "_hash_confirmation_code", lambda *args: "code-hash")

    user_repo = SimpleNamespace(get_user_by_email=AsyncMock(return_value=None))
    confirmation_repo = SimpleNamespace(
        upsert_confirmation=AsyncMock(),
        delete_by_email=AsyncMock(),
    )
    mail_service = SimpleNamespace(send_registration_confirmation=AsyncMock(side_effect=_send))

    service = _make_service(user_repo, confirmation_repo, mail_service)

    with pytest.raises(ServiceUnavailableError):
        run(service.register(UserCreate(email="user@example.com", password="pw")))

    confirmation_repo.delete_by_email.assert_awaited_once_with("user@example.com")


def test_confirm_registration_success_creates_user_and_returns_token(monkeypatch):
    user_id = uuid4()
    confirmation = SimpleNamespace(
        hashed_password="hashed-pw",
        code_hash="code-hash",
        attempts=0,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    created_user = SimpleNamespace(id=user_id, email="user@example.com", role=UserRoles.user, roles=[])
    user_repo = SimpleNamespace(
        get_user_by_email=AsyncMock(side_effect=[None, created_user]),
        create_user=AsyncMock(return_value=created_user),
    )
    confirmation_repo = SimpleNamespace(
        get_by_email=AsyncMock(return_value=confirmation),
        increment_attempts=AsyncMock(),
        delete_by_email=AsyncMock(),
    )

    monkeypatch.setattr(AuthService, "_hash_confirmation_code", lambda *args: "code-hash")
    monkeypatch.setattr("app.core.services.auth_service.create_access_token", lambda *_: "access-token")
    monkeypatch.setattr("app.core.services.auth_service.create_refresh_token", lambda *_: "refresh-token")

    service = _make_service(user_repo, confirmation_repo)
    token = run(
        service.confirm_registration(
            RegistrationConfirmRequest(email="user@example.com", code="123456")
        )
    )

    created_arg = user_repo.create_user.call_args.args[0]
    assert str(created_arg.email) == "user@example.com"
    assert created_arg.password == "hashed-pw"
    confirmation_repo.delete_by_email.assert_awaited_once_with("user@example.com")
    assert token.access_token == "access-token"
    assert token.refresh_token == "refresh-token"


def test_confirm_registration_rejects_missing_confirmation():
    user_repo = SimpleNamespace(get_user_by_email=AsyncMock(return_value=None))
    confirmation_repo = SimpleNamespace(get_by_email=AsyncMock(return_value=None))
    service = _make_service(user_repo, confirmation_repo)

    with pytest.raises(ValidationError):
        run(
            service.confirm_registration(
                RegistrationConfirmRequest(email="user@example.com", code="123456")
            )
        )


def test_confirm_registration_deletes_expired_confirmation():
    confirmation = SimpleNamespace(
        hashed_password="hashed-pw",
        code_hash="code-hash",
        attempts=0,
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    user_repo = SimpleNamespace(get_user_by_email=AsyncMock(return_value=None))
    confirmation_repo = SimpleNamespace(
        get_by_email=AsyncMock(return_value=confirmation),
        delete_by_email=AsyncMock(),
    )
    service = _make_service(user_repo, confirmation_repo)

    with pytest.raises(ValidationError):
        run(
            service.confirm_registration(
                RegistrationConfirmRequest(email="user@example.com", code="123456")
            )
        )

    confirmation_repo.delete_by_email.assert_awaited_once_with("user@example.com")


def test_confirm_registration_increments_attempts_for_invalid_code(monkeypatch):
    confirmation = SimpleNamespace(
        hashed_password="hashed-pw",
        code_hash="code-hash",
        attempts=0,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    user_repo = SimpleNamespace(get_user_by_email=AsyncMock(return_value=None))
    confirmation_repo = SimpleNamespace(
        get_by_email=AsyncMock(return_value=confirmation),
        increment_attempts=AsyncMock(return_value=1),
        delete_by_email=AsyncMock(),
    )

    monkeypatch.setattr(AuthService, "_hash_confirmation_code", lambda *args: "other-code-hash")

    service = _make_service(user_repo, confirmation_repo)

    with pytest.raises(ValidationError):
        run(
            service.confirm_registration(
                RegistrationConfirmRequest(email="user@example.com", code="123456")
            )
        )

    confirmation_repo.increment_attempts.assert_awaited_once_with("user@example.com")
    confirmation_repo.delete_by_email.assert_not_awaited()


def test_login_invalid_email_raises():
    user_repo = SimpleNamespace(get_user_by_email=AsyncMock(return_value=None))
    service = _make_service(user_repo)

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

    async def _verify(*_):
        return False

    monkeypatch.setattr("app.core.services.auth_service.verify_password_async", _verify)

    service = _make_service(user_repo)
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

    async def _verify(*_):
        return True

    monkeypatch.setattr("app.core.services.auth_service.verify_password_async", _verify)
    monkeypatch.setattr("app.core.services.auth_service.create_access_token", lambda *_: "token")
    monkeypatch.setattr("app.core.services.auth_service.create_refresh_token", lambda *_: "refresh")

    service = _make_service(user_repo)
    token = run(service.login(LoginRequest(email="user@example.com", password="pw")))

    assert token.access_token == "token"
    assert token.refresh_token == "refresh"


def test_refresh_success_returns_new_access_token(monkeypatch):
    user_id = uuid4()
    user_repo = SimpleNamespace()

    monkeypatch.setattr(
        "app.core.services.auth_service.decode_token",
        lambda *_: {"type": "refresh", "sub": str(user_id), "roles": ["user"], "permissions": ["read"]},
    )
    monkeypatch.setattr("app.core.services.auth_service.create_access_token", lambda *_: "new-access")

    service = _make_service(user_repo)
    token = run(service.refresh(RefreshTokenRequest(refresh_token="refresh")))

    assert token.access_token == "new-access"
    assert token.refresh_token is None


def test_refresh_rejects_access_token(monkeypatch):
    user_repo = SimpleNamespace()

    monkeypatch.setattr(
        "app.core.services.auth_service.decode_token",
        lambda *_: {"type": "access", "sub": str(uuid4())},
    )

    service = _make_service(user_repo)

    with pytest.raises(UnauthorizedError):
        run(service.refresh(RefreshTokenRequest(refresh_token="access")))
