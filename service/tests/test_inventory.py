from app.ansible.inventory import build_inventory
from app.models import Target


def target(**overrides: object) -> Target:
    values: dict[str, object] = {
        "name": "target1",
        "host": "target1",
        "port": 22,
        "username": "ansible",
        "auth_type": "ssh_key",
        "ssh_private_key_path": "/opt/roller/ssh/id_rsa",
        "python_interpreter": "/usr/bin/python3",
    }
    values.update(overrides)
    return Target(**values)


def test_inventory_contains_target_host() -> None:
    inventory = build_inventory(target(host="target1"))

    assert "target1 ansible_host=target1" in inventory


def test_inventory_contains_target_username() -> None:
    inventory = build_inventory(target(username="ansible"))

    assert "ansible_user=ansible" in inventory


def test_inventory_contains_private_key_path() -> None:
    inventory = build_inventory(target(ssh_private_key_path="/opt/roller/ssh/id_rsa"))

    assert "ansible_ssh_private_key_file=/opt/roller/ssh/id_rsa" in inventory
