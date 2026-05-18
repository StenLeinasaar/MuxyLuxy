import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from app.ansible.playbook import generate_run_files
from app.config import settings
from app.database import SessionLocal
from app.metrics.prometheus import (
    ACTIVE_RUNS,
    RUN_DURATION_SECONDS,
    RUNS_TOTAL,
)
from app.models import Role, Run, Target

STATUS_IN_PROGRESS = "in_progress"
STATUS_SUCCESSFUL = "successful"
STATUS_FAILED = "failed"


def _log_path_for_run(run_id: str) -> Path:
    log_root = Path(settings.roller_run_log_dir)
    log_root.mkdir(parents=True, exist_ok=True)
    return log_root / f"{run_id}.log"


def execute_run_background(run_pk: int) -> None:
    with SessionLocal() as db:
        run = db.get(Run, run_pk)
        if run is None:
            return

        target = db.get(Target, run.target_id)
        role = db.get(Role, run.role_id)
        if target is None or role is None:
            run.status = STATUS_FAILED
            run.finished_at = datetime.now(UTC)
            run.error_message = "Target or role no longer exists"
            db.commit()
            RUNS_TOTAL.labels(status="failed").inc()
            return

        run.status = STATUS_IN_PROGRESS
        run.started_at = datetime.now(UTC)
        log_path = _log_path_for_run(run.run_id)
        run.log_path = str(log_path)
        db.commit()

        ACTIVE_RUNS.inc()
        run_started_monotonic = time.monotonic()
        try:
            generated_files = generate_run_files(target, role, run_id=run.run_id)
            env = os.environ.copy()
            env["ANSIBLE_ROLES_PATH"] = settings.ansible_roles_path
            ansible_cfg = (
                Path(settings.ansible_root).expanduser().resolve() / "ansible.cfg"
            )
            if ansible_cfg.is_file():
                env["ANSIBLE_CONFIG"] = str(ansible_cfg)
            env["ANSIBLE_HOST_KEY_CHECKING"] = "False"

            with log_path.open("w", encoding="utf-8") as log_file:
                process = subprocess.Popen(
                    [
                        "ansible-playbook",
                        "-i",
                        str(generated_files.inventory_path),
                        str(generated_files.playbook_path),
                    ],
                    cwd=str(generated_files.run_directory),
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env,
                )

                try:
                    exit_code = process.wait(
                        timeout=settings.ansible_run_timeout_seconds,
                    )
                except subprocess.TimeoutExpired:
                    process.kill()
                    exit_code = process.wait()
                    log_file.write(
                        "\nAnsible run timed out after "
                        f"{settings.ansible_run_timeout_seconds} seconds.\n",
                    )
                    run.error_message = "Ansible run timed out"

            run.exit_code = exit_code
            run.status = STATUS_SUCCESSFUL if exit_code == 0 else STATUS_FAILED
        except Exception as exc:
            run.status = STATUS_FAILED
            run.error_message = str(exc)
        finally:
            ACTIVE_RUNS.dec()
            RUN_DURATION_SECONDS.observe(time.monotonic() - run_started_monotonic)
            run_terminal = "successful" if run.status == STATUS_SUCCESSFUL else "failed"
            RUNS_TOTAL.labels(status=run_terminal).inc()
            run.finished_at = datetime.now(UTC)
            db.commit()
