from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.auth import seed_admin_user
from app.database import SessionLocal
from app.main import app
from app.models import Role, Run, Target

TARGET_NAMES = ("target1",)
ROLE_NAMES = ("base", "disabled-role")


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


def seed_target_and_role(*, role_enabled: bool = True) -> None:
    with SessionLocal() as db:
        db.add(
            Target(
                name="target1",
                host="target1",
                port=22,
                username="ansible",
                auth_type="ssh_key",
                ssh_private_key_path="/opt/roller/ssh/id_rsa",
                python_interpreter="/usr/bin/python3",
            )
        )
        db.add(
            Role(
                name="base" if role_enabled else "disabled-role",
                description="Demo role",
                path="/opt/ansible/roles/base",
                enabled=role_enabled,
            )
        )
        db.commit()


def run_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "target_name": "target1",
        "role_name": "base",
    }
    payload.update(overrides)
    return payload


def test_post_run_requires_authentication(client: TestClient) -> None:
    response = client.post("/run", json=run_payload())

    assert response.status_code == 401


def test_post_run_rejects_unknown_target(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    seed_target_and_role()

    response = client.post(
        "/run",
        headers=auth_headers,
        json=run_payload(target_name="missing-target"),
    )

    assert response.status_code == 404


def test_post_run_rejects_unknown_role(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    seed_target_and_role()

    response = client.post(
        "/run",
        headers=auth_headers,
        json=run_payload(role_name="missing-role"),
    )

    assert response.status_code == 404


def test_post_run_rejects_disabled_role(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    seed_target_and_role(role_enabled=False)

    response = client.post(
        "/run",
        headers=auth_headers,
        json=run_payload(role_name="disabled-role"),
    )

    assert response.status_code == 400


def test_post_run_creates_queued_run(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queued_run_ids: list[int] = []

    def fake_execute_run_background(run_pk: int) -> None:
        queued_run_ids.append(run_pk)

    monkeypatch.setattr(
        "app.api.runs.execute_run_background",
        fake_execute_run_background,
    )
    seed_target_and_role()

    response = client.post("/run", headers=auth_headers, json=run_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert body["run_id"]
    assert queued_run_ids

    with SessionLocal() as db:
        run = db.scalar(select(Run).where(Run.run_id == body["run_id"]))

    assert run is not None
    assert run.status == "queued"
