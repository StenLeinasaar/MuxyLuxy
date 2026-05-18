import re
from pathlib import Path

from app.models import Target


INVENTORY_FILENAME = "inventory.ini"
DEFAULT_PYTHON_INTERPRETER = "/usr/bin/python3"
SAFE_INVENTORY_HOST_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
SAFE_INVENTORY_VALUE_PATTERN = re.compile(r"^[^\s=]+$")


class InventoryGenerationError(ValueError):
    pass


def _validate_single_line(value: str, field_name: str) -> str:
    if not value:
        raise InventoryGenerationError(f"{field_name} is required")

    if any(character in value for character in "\r\n"):
        raise InventoryGenerationError(f"{field_name} must be a single line")

    return value


def _validate_inventory_value(value: str, field_name: str) -> str:
    value = _validate_single_line(value, field_name)
    if not SAFE_INVENTORY_VALUE_PATTERN.fullmatch(value):
        raise InventoryGenerationError(
            f"{field_name} must not contain whitespace or equals signs",
        )

    return value


def _validate_host_alias(value: str) -> str:
    value = _validate_single_line(value, "target name")
    if not SAFE_INVENTORY_HOST_PATTERN.fullmatch(value):
        raise InventoryGenerationError(
            "target name may only contain letters, numbers, dots, underscores, and hyphens",
        )

    return value


def build_inventory(target: Target) -> str:
    target_name = _validate_host_alias(target.name)
    host = _validate_inventory_value(target.host, "target host")
    username = _validate_inventory_value(target.username, "target username")
    private_key_path = _validate_inventory_value(
        target.ssh_private_key_path or "",
        "target private key path",
    )
    python_interpreter = _validate_inventory_value(
        target.python_interpreter or DEFAULT_PYTHON_INTERPRETER,
        "target Python interpreter",
    )

    return (
        "[target]\n"
        f"{target_name} "
        f"ansible_host={host} "
        f"ansible_port={target.port} "
        f"ansible_user={username} "
        f"ansible_ssh_private_key_file={private_key_path} "
        f"ansible_python_interpreter={python_interpreter}\n"
    )


def write_inventory(target: Target, run_directory: Path) -> Path:
    inventory_path = run_directory / INVENTORY_FILENAME
    inventory_path.write_text(build_inventory(target), encoding="utf-8")
    return inventory_path
