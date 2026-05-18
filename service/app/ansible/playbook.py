from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.ansible.inventory import INVENTORY_FILENAME, build_inventory
from app.ansible.validation import SAFE_ROLE_NAME_PATTERN
from app.config import settings
from app.models import Role, Target


PLAYBOOK_FILENAME = "playbook.yml"


class PlaybookGenerationError(ValueError):
    pass


@dataclass(frozen=True)
class GeneratedAnsibleFiles:
    run_id: str
    run_directory: Path
    inventory_path: Path
    playbook_path: Path


def generate_run_id() -> str:
    return uuid4().hex


def build_playbook(role: Role) -> str:
    if not SAFE_ROLE_NAME_PATTERN.fullmatch(role.name):
        raise PlaybookGenerationError(
            "role name may only contain letters, numbers, underscores, and hyphens",
        )

    return (
        "---\n"
        "- name: Apply requested role\n"
        "  hosts: target\n"
        "  gather_facts: true\n"
        "  become: true\n"
        "  roles:\n"
        f"    - role: {role.name}\n"
    )


def write_playbook(role: Role, run_directory: Path) -> Path:
    playbook_path = run_directory / PLAYBOOK_FILENAME
    playbook_path.write_text(build_playbook(role), encoding="utf-8")
    return playbook_path


def generate_run_files(
    target: Target,
    role: Role,
    generated_root: str | Path | None = None,
    run_id: str | None = None,
) -> GeneratedAnsibleFiles:
    root = Path(generated_root or settings.ansible_generated_path)
    run_id = run_id or generate_run_id()
    run_directory = root / run_id

    inventory_content = build_inventory(target)
    playbook_content = build_playbook(role)

    run_directory.mkdir(parents=True, exist_ok=False)
    inventory_path = run_directory / INVENTORY_FILENAME
    playbook_path = run_directory / PLAYBOOK_FILENAME
    inventory_path.write_text(inventory_content, encoding="utf-8")
    playbook_path.write_text(playbook_content, encoding="utf-8")

    return GeneratedAnsibleFiles(
        run_id=run_id,
        run_directory=run_directory,
        inventory_path=inventory_path,
        playbook_path=playbook_path,
    )
