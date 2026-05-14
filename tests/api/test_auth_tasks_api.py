from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_auth_register_confirm_and_login(api_test_state):
    email = f"api_smoke_{uuid4().hex}@example.com"
    password = "12345678"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        register_response = await client.post(
            "/auth/register",
            json={"email": email, "password": password, "role": "user"},
        )
        assert register_response.status_code == 202
        register_body = register_response.json()
        assert register_body == {"detail": "Registration confirmation code sent"}

        confirm_response = await client.post(
            "/auth/register/confirm",
            json={"email": email, "code": api_test_state.mail_service.registration_codes[email]},
        )
        assert confirm_response.status_code == 201
        confirm_body = confirm_response.json()
        assert confirm_body.get("access_token")
        assert confirm_body.get("refresh_token")
        assert confirm_body.get("token_type") == "bearer"

        login_response = await client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        assert login_response.status_code == 200
        login_body = login_response.json()
        assert login_body.get("access_token")
        assert login_body.get("refresh_token")
        assert login_body.get("token_type") == "bearer"


async def test_tasks_list_requires_auth_and_returns_list(api_test_state):
    email = f"api_tasks_{uuid4().hex}@example.com"
    password = "12345678"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        register_response = await client.post(
            "/auth/register",
            json={"email": email, "password": password, "role": "user"},
        )
        assert register_response.status_code == 202

        confirm_response = await client.post(
            "/auth/register/confirm",
            json={"email": email, "code": api_test_state.mail_service.registration_codes[email]},
        )
        assert confirm_response.status_code == 201
        access_token = confirm_response.json()["access_token"]

        unauthorized_response = await client.get("/tasks/")
        assert unauthorized_response.status_code == 401

        authorized_response = await client.get(
            "/tasks/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert authorized_response.status_code == 200
        assert isinstance(authorized_response.json(), list)
