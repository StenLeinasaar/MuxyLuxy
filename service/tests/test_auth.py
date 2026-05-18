from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.auth import seed_admin_user
from app.database import SessionLocal
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with SessionLocal() as db:
        seed_admin_user(db)

    with TestClient(app) as test_client:
        yield test_client


def test_valid_login_returns_access_token(client: TestClient) -> None:
    response = client.post(
        "/login",
        json={"username": "admin", "password": "admin"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_invalid_password_returns_401(client: TestClient) -> None:
    response = client.post(
        "/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_missing_token_on_protected_endpoint_returns_401(client: TestClient) -> None:
    response = client.get("/me")

    assert response.status_code == 401


def test_invalid_token_returns_401(client: TestClient) -> None:
    response = client.get(
        "/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
