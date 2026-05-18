from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.auth import seed_admin_user
from app.config import settings
from app.database import SessionLocal
from app.main import app
from app.models import Role


ROLE_NAMES = ("role1", "missing-tasks", "disabled-role")


@pytest.fixture()
def roles_root(tmp_path: Path) -> Generator[Path, None, None]:
    original_roles_path = settings.ansible_roles_path
    root = tmp_path / "roles"
    root.mkdir()
    settings.ansible_roles_path = str(root)

    yield root

    settings.ansible_roles_path = original_roles_path


@pytest.fixture()
def client(roles_root: Path) -> Generator[TestClient, None, None]:
    with SessionLocal() as db:
        seed_admin_user(db)
        db.execute(delete(Role).where(Role.name.in_(ROLE_NAMES)))
        db.commit()

    with TestClient(app) as test_client:
        yield test_client

    with SessionLocal() as db:
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


def create_role_path(root: Path, name: str) -> Path:
    role_path = root / name
    tasks_path = role_path / "tasks"
    tasks_path.mkdir(parents=True)
    (tasks_path / "main.yml").write_text("---\n- ansible.builtin.debug:\n    msg: ok\n")
    return role_path


def role_payload(path: Path, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "path": str(path),
        "description": "Demo role",
    }
    payload.update(overrides)
    return payload


def test_get_roles_returns_list(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get("/roles", headers=auth_headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_put_valid_role_creates_role(
    client: TestClient,
    auth_headers: dict[str, str],
    roles_root: Path,
) -> None:
    path = create_role_path(roles_root, "role1")

    response = client.put(
        "/roles/role1",
        headers=auth_headers,
        json=role_payload(path),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "role1"
    assert body["path"] == str(path.resolve())
    assert body["description"] == "Demo role"
    assert body["enabled"] is True


def test_put_existing_role_updates_role(
    client: TestClient,
    auth_headers: dict[str, str],
    roles_root: Path,
) -> None:
    initial_path = create_role_path(roles_root, "role1")
    updated_path = create_role_path(roles_root, "role1-updated")
    client.put(
        "/roles/role1",
        headers=auth_headers,
        json=role_payload(initial_path),
    )

    response = client.put(
        "/roles/role1",
        headers=auth_headers,
        json=role_payload(updated_path, description="Updated role"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "role1"
    assert body["path"] == str(updated_path.resolve())
    assert body["description"] == "Updated role"
    assert body["enabled"] is True


def test_put_invalid_path_outside_role_root_is_rejected(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
) -> None:
    outside_path = create_role_path(tmp_path / "outside", "role1")

    response = client.put(
        "/roles/role1",
        headers=auth_headers,
        json=role_payload(outside_path),
    )

    assert response.status_code == 400


def test_put_missing_tasks_main_yml_is_rejected(
    client: TestClient,
    auth_headers: dict[str, str],
    roles_root: Path,
) -> None:
    path = roles_root / "missing-tasks"
    path.mkdir()

    response = client.put(
        "/roles/missing-tasks",
        headers=auth_headers,
        json=role_payload(path),
    )

    assert response.status_code == 400


def test_delete_disables_role(
    client: TestClient,
    auth_headers: dict[str, str],
    roles_root: Path,
) -> None:
    path = create_role_path(roles_root, "disabled-role")
    client.put(
        "/roles/disabled-role",
        headers=auth_headers,
        json=role_payload(path),
    )

    response = client.delete("/roles/disabled-role", headers=auth_headers)

    assert response.status_code == 204


def test_disabled_role_still_appears_with_enabled_false(
    client: TestClient,
    auth_headers: dict[str, str],
    roles_root: Path,
) -> None:
    path = create_role_path(roles_root, "disabled-role")
    client.put(
        "/roles/disabled-role",
        headers=auth_headers,
        json=role_payload(path),
    )
    client.delete("/roles/disabled-role", headers=auth_headers)

    response = client.get("/roles", headers=auth_headers)

    assert response.status_code == 200
    roles = response.json()
    assert any(
        role["name"] == "disabled-role" and role["enabled"] is False
        for role in roles
    )
