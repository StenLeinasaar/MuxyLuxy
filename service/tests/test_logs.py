from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.auth import seed_admin_user
from app.database import SessionLocal
from app.main import app
from app.models import Role, Run, Target

TARGET_NAMES = ("log-target1",)
ROLE_NAMES = ("log-role1",)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with SessionLocal() as db:
        seed_admin_user(db)
        db.execute(delete(Run))
        db.execute(delete(Target).where(Target.name.in_(TARGET_NAMES)))
        db.execute(delete(Role).where(Role.name.in_(ROLE_NAMES)))
        db.commit()

    with TestClient(app) as test_client:
        yield test_client

    with SessionLocal() as db:
        db.execute(delete(Run))
        db.execute(delete(Target).where(Target.name.in_(TARGET_NAMES)))
        db.execute(delete(Role).where(Role.name.in_(ROLE_NAMES)))
        db.commit()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/login",
        json={"username": "admin", "password": "admin"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_status_requires_authentication(client: TestClient) -> None:
    response = client.get("/status")

    assert response.status_code == 401


def test_get_status_returns_list(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get("/status", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_get_logs_requires_authentication(client: TestClient) -> None:
    response = client.get("/logs", params={"run_id": "any"})

    assert response.status_code == 401


def test_get_logs_returns_404_for_unknown_run_id(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(
        "/logs",
        headers=auth_headers,
        params={"run_id": "unknown-run-id"},
    )

    assert response.status_code == 404


def test_get_logs_returns_content_for_existing_log(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "run.log"
    log_file.write_text("playbook output line 1\n", encoding="utf-8")

    with SessionLocal() as db:
        target = Target(
            name="log-target1",
            host="h1",
            port=22,
            username="u",
            auth_type="ssh_key",
            ssh_private_key_path="/key",
        )
        role = Role(
            name="log-role1",
            description=None,
            path="/role",
            enabled=True,
        )
        db.add(target)
        db.add(role)
        db.flush()
        run = Run(
            run_id="testrunid01",
            target_id=target.id,
            role_id=role.id,
            status="successful",
            exit_code=0,
            log_path=str(log_file),
        )
        db.add(run)
        db.commit()

    response = client.get(
        "/logs",
        headers=auth_headers,
        params={"run_id": "testrunid01"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == "testrunid01"
    assert body["status"] == "successful"
    assert body["exit_code"] == 0
    assert body["stdout"] == "playbook output line 1\n"
    assert body["log_path"] == str(log_file)
