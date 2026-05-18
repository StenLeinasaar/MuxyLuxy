from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_returns_200() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200


def test_healthz_contains_status_ok() -> None:
    response = client.get("/healthz")
    body = response.json()
    assert body.get("status") == "ok"


def test_healthz_database_ok() -> None:
    response = client.get("/healthz")
    assert response.json().get("database") == "ok"
