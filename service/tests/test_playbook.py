from pathlib import Path

from app.ansible.playbook import build_playbook, generate_run_files
from app.config import settings
from app.models import Role, Target


def target() -> Target:
    return Target(
        name="target1",
        host="target1",
        port=22,
        username="ansible",
        auth_type="ssh_key",
        ssh_private_key_path="/opt/roller/ssh/id_rsa",
        python_interpreter="/usr/bin/python3",
    )


def role(**overrides: object) -> Role:
    values: dict[str, object] = {
        "name": "base",
        "description": None,
        "path": "/opt/roller/roles/base",
        "enabled": True,
    }
    values.update(overrides)
    return Role(**values)


def test_playbook_contains_selected_role() -> None:
    playbook = build_playbook(role(name="base"))

    assert "    - role: base\n" in playbook


def test_playbook_does_not_include_arbitrary_user_input() -> None:
    playbook = build_playbook(
        role(
            description="arbitrary user input",
            path="/tmp/arbitrary-user-input",
        ),
    )

    assert "arbitrary user input" not in playbook
    assert "/tmp/arbitrary-user-input" not in playbook


def test_generated_files_are_created_under_configured_generated_path(
    tmp_path: Path,
) -> None:
    original_generated_path = settings.ansible_generated_path
    settings.ansible_generated_path = str(tmp_path / "generated")

    try:
        generated_files = generate_run_files(target(), role())
    finally:
        settings.ansible_generated_path = original_generated_path

    configured_root = tmp_path / "generated"
    assert generated_files.run_directory.parent == configured_root
    assert generated_files.inventory_path == generated_files.run_directory / "inventory.ini"
    assert generated_files.playbook_path == generated_files.run_directory / "playbook.yml"
    assert generated_files.inventory_path.is_file()
    assert generated_files.playbook_path.is_file()
