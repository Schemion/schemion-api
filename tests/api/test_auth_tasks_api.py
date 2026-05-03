from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_auth_register_and_login():
    client = TestClient(app)
    email = f"api_smoke_{uuid4().hex}@example.com"
    password = "12345678"

    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": password, "role": "user"},
    )
    assert register_response.status_code == 201
    register_body = register_response.json()
    assert register_body.get("access_token")
    assert register_body.get("refresh_token")
    assert register_body.get("token_type") == "bearer"

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body.get("access_token")
    assert login_body.get("refresh_token")
    assert login_body.get("token_type") == "bearer"


def test_tasks_list_requires_auth_and_returns_list():
    client = TestClient(app)
    email = f"api_tasks_{uuid4().hex}@example.com"
    password = "12345678"

    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": password, "role": "user"},
    )
    assert register_response.status_code == 201
    access_token = register_response.json()["access_token"]

    unauthorized_response = client.get("/tasks/")
    assert unauthorized_response.status_code == 401

    authorized_response = client.get(
        "/tasks/?skip=0&limit=10",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert authorized_response.status_code == 200
    assert isinstance(authorized_response.json(), list)
