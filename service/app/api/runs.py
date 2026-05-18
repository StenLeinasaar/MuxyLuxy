from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
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
