import re
from pathlib import Path


SAFE_ROLE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class RoleValidationError(ValueError):
    pass


def validate_role_path(
    role_name: str,
    role_path: str,
    roles_root: str,
) -> str:
    if not SAFE_ROLE_NAME_PATTERN.fullmatch(role_name):
        raise RoleValidationError(
            "Role name may only contain letters, numbers, underscores, and hyphens",
        )

    resolved_roles_root = Path(roles_root).expanduser().resolve()
    resolved_role_path = Path(role_path).expanduser().resolve()

    if not resolved_role_path.is_relative_to(resolved_roles_root):
        raise RoleValidationError("Role path must be inside ANSIBLE_ROLES_PATH")

    if not resolved_role_path.exists():
        raise RoleValidationError("Role path does not exist")

    if not resolved_role_path.is_dir():
        raise RoleValidationError("Role path must be a directory")

    if not (resolved_role_path / "tasks" / "main.yml").is_file():
        raise RoleValidationError("Role must contain tasks/main.yml")

    return str(resolved_role_path)
