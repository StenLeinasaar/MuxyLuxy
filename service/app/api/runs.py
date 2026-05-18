from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ansible.playbook import generate_run_id
from app.ansible.runner import execute_run_background
from app.auth import get_current_user
from app.database import get_db
from app.models import Role, Run, Target

STATUS_QUEUED = "queued"

router = APIRouter(dependencies=[Depends(get_current_user)])


class RunRequest(BaseModel):
    target_name: str = Field(min_length=1)
    role_name: str = Field(min_length=1)


class RunResponse(BaseModel):
    run_id: str
    status: str


class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    exit_code: int | None
    log_path: str | None


@router.post("/run", response_model=RunResponse)
def create_run(
    payload: RunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> RunResponse:
    target = db.scalar(select(Target).where(Target.name == payload.target_name))
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    role = db.scalar(select(Role).where(Role.name == payload.role_name))
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    if not role.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role is disabled",
        )

    run = Run(
        run_id=generate_run_id(),
        target_id=target.id,
        role_id=role.id,
        status=STATUS_QUEUED,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    background_tasks.add_task(execute_run_background, run.id)
    return RunResponse(run_id=run.run_id, status=STATUS_QUEUED)


@router.get("/status", response_model=list[RunStatusResponse])
def list_run_statuses(db: Session = Depends(get_db)) -> list[RunStatusResponse]:
    runs = db.scalars(select(Run).order_by(Run.created_at.desc(), Run.id.desc())).all()
    return [
        RunStatusResponse(
            run_id=run.run_id,
            status=run.status,
            exit_code=run.exit_code,
            log_path=run.log_path,
        )
        for run in runs
    ]


@router.get("/logs", response_model=None)
def get_run_logs(
    run_id: str = Query(min_length=1),
    db: Session = Depends(get_db),
) -> Response:
    run = db.scalar(select(Run).where(Run.run_id == run_id))
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    if run.log_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run log not found",
        )

    log_path = Path(run.log_path)
    if not log_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run log not found",
        )

    return Response(
        content=log_path.read_text(encoding="utf-8"),
        media_type="text/plain",
    )
