from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.auth import seed_admin_user
from app.database import SessionLocal
from app.main import app
from app.models import Target


TARGET_NAMES = ("target1",)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with SessionLocal() as db:
        seed_admin_user(db)
        db.execute(delete(Target).where(Target.name.in_(TARGET_NAMES)))
        db.commit()

    with TestClient(app) as test_client:
        yield test_client

    with SessionLocal() as db:
        db.execute(delete(Target).where(Target.name.in_(TARGET_NAMES)))
        db.commit()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/login",
        json={"username": "admin", "password": "admin"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def target_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "host": "target1",
        "port": 22,
        "username": "ansible",
        "auth_type": "ssh_key",
        "ssh_private_key_path": "/opt/roller/ssh/id_rsa",
        "python_interpreter": "/usr/bin/python3",
    }
    payload.update(overrides)
    return payload


def test_get_targets_initially_returns_list(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get("/targets", headers=auth_headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_put_target_creates_target(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.put(
        "/targets/target1",
        headers=auth_headers,
        json=target_payload(port=22, python_interpreter="/usr/bin/python3"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "target1"
    assert body["host"] == "target1"
    assert body["port"] == 22
    assert body["python_interpreter"] == "/usr/bin/python3"


def test_put_target_updates_target(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    client.put("/targets/target1", headers=auth_headers, json=target_payload())

    response = client.put(
        "/targets/target1",
        headers=auth_headers,
        json=target_payload(host="target1.example.com", port=2222),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "target1"
    assert body["host"] == "target1.example.com"
    assert body["port"] == 2222


def test_delete_target_removes_target(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    client.put("/targets/target1", headers=auth_headers, json=target_payload())

    delete_response = client.delete("/targets/target1", headers=auth_headers)
    list_response = client.get("/targets", headers=auth_headers)

    assert delete_response.status_code == 204
    assert all(target["name"] != "target1" for target in list_response.json())


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("GET", "/targets", None),
        ("PUT", "/targets/target1", target_payload()),
        ("DELETE", "/targets/target1", None),
    ],
)
def test_unauthenticated_requests_fail(
    client: TestClient,
    method: str,
    path: str,
    json: dict[str, object] | None,
) -> None:
    response = client.request(method, path, json=json)

    assert response.status_code == 401


def test_invalid_target_payload_returns_validation_error(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.put(
        "/targets/target1",
        headers=auth_headers,
        json={"host": "target1", "auth_type": "password"},
    )

    assert response.status_code in {400, 422}
