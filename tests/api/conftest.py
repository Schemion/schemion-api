from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from dishka import Provider, Scope, make_async_container, provide

from app.core.interfaces import IMailService
from app.core.services import TaskService
from app.core.services.auth_service import AuthService
from app.main import app


class _ApiTestState:
    def __init__(self):
        self.user_repo = _InMemoryUserRepository()
        self.confirmation_repo = _InMemoryRegistrationConfirmationRepository()
        self.mail_service = _CapturingMailService()
        self.task_repo = _InMemoryTaskRepository()
        self.cache = _NoopCache()
        self.storage = _NoopStorage()
        self.model_repo = SimpleNamespace()
        self.dataset_repo = SimpleNamespace()
        self.bobber = SimpleNamespace()


class _InMemoryUserRepository:
    def __init__(self):
        self._users_by_email = {}

    async def create_user(self, user):
        created = SimpleNamespace(
            id=uuid4(),
            email=str(user.email),
            hashed_password=user.password,
            roles=[],
        )
        self._users_by_email[created.email] = created
        return created

    async def get_user_by_email(self, email: str):
        return self._users_by_email.get(str(email))

    async def get_user_by_id(self, user_id):
        return next((user for user in self._users_by_email.values() if user.id == user_id), None)

    async def get_user_datasets(self, _user_id):
        return []

    async def get_user_models(self, _user_id):
        return []


class _InMemoryRegistrationConfirmationRepository:
    def __init__(self):
        self._confirmations_by_email = {}

    async def get_by_email(self, email: str):
        return self._confirmations_by_email.get(str(email))

    async def upsert_confirmation(
        self,
        email: str,
        hashed_password: str,
        code_hash: str,
        expires_at: datetime,
    ):
        confirmation = SimpleNamespace(
            email=email,
            hashed_password=hashed_password,
            code_hash=code_hash,
            attempts=0,
            expires_at=expires_at,
        )
        self._confirmations_by_email[email] = confirmation
        return confirmation

    async def increment_attempts(self, email: str) -> int:
        confirmation = self._confirmations_by_email[email]
        confirmation.attempts += 1
        return confirmation.attempts

    async def delete_by_email(self, email: str) -> None:
        self._confirmations_by_email.pop(str(email), None)


class _CapturingMailService(IMailService):
    def __init__(self):
        self.registration_codes = {}

    async def send_registration_confirmation(self, email: str, code: str) -> None:
        self.registration_codes[email] = code


class _InMemoryTaskRepository:
    async def get_tasks(self, skip: int = 0, limit: int = 100, user_id=None, model_id=None):
        return []


class _NoopCache:
    async def get(self, _key):
        return None

    async def set(self, _key, _value, expire=None) -> None:
        return None

    async def delete(self, _key) -> None:
        return None

    async def delete_pattern(self, _pattern) -> None:
        return None


class _NoopStorage:
    async def get_presigned_file_url(self, *_args, **_kwargs):
        return "http://testserver/files/task-output"


class _ApiTestProvider(Provider):
    def __init__(self, state: _ApiTestState):
        super().__init__()
        self.state = state

    @provide(scope=Scope.REQUEST)
    def auth_service(self) -> AuthService:
        return AuthService(
            self.state.user_repo,
            self.state.confirmation_repo,
            self.state.mail_service,
        )

    @provide(scope=Scope.REQUEST)
    def task_service(self) -> TaskService:
        return TaskService(
            task_repo=self.state.task_repo,
            storage=self.state.storage,
            model_repo=self.state.model_repo,
            dataset_repo=self.state.dataset_repo,
            cache_repo=self.state.cache,
            bobber_publisher=self.state.bobber,
        )


@pytest.fixture
def api_test_state():
    return _ApiTestState()


@pytest.fixture(autouse=True)
async def use_api_test_container(api_test_state, monkeypatch):
    async def get_password_hash_for_test(password: str) -> str:
        return f"hashed:{password}"

    async def verify_password_for_test(password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed:{password}"

    monkeypatch.setattr(
        "app.core.services.auth_service.get_password_hash_async",
        get_password_hash_for_test,
    )
    monkeypatch.setattr(
        "app.core.services.auth_service.verify_password_async",
        verify_password_for_test,
    )

    original_container = app.state.dishka_container
    test_container = make_async_container(_ApiTestProvider(api_test_state))
    app.state.dishka_container = test_container
    try:
        yield
    finally:
        app.state.dishka_container = original_container
        await test_container.close()
