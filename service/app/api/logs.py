from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Run, Target

router = APIRouter(dependencies=[Depends(get_current_user)])


class RunStatusItem(BaseModel):
    run_id: str
    status: str
    exit_code: int | None
    log_path: str | None


class RunLogResponse(BaseModel):
    run_id: str
    status: str
    exit_code: int | None
    stdout: str
    log_path: str


@router.get("/status", response_model=list[RunStatusItem])
def list_recent_runs(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=500),
    run_status: str | None = Query(default=None, alias="status", min_length=1),
    target_name: str | None = Query(default=None, min_length=1),
) -> list[RunStatusItem]:
    stmt = select(Run)
    if target_name is not None:
        stmt = stmt.join(Target, Run.target_id == Target.id).where(Target.name == target_name)
    if run_status is not None:
        stmt = stmt.where(Run.status == run_status)
    stmt = stmt.order_by(Run.created_at.desc(), Run.id.desc()).limit(limit)
    runs = db.scalars(stmt).all()
    return [
        RunStatusItem(
            run_id=run.run_id,
            status=run.status,
            exit_code=run.exit_code,
            log_path=run.log_path,
        )
        for run in runs
    ]


@router.get("/logs", response_model=RunLogResponse)
def get_run_log(
    run_id: str = Query(min_length=1),
    db: Session = Depends(get_db),
) -> RunLogResponse:
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

    stdout = log_path.read_text(encoding="utf-8")
    return RunLogResponse(
        run_id=run.run_id,
        status=run.status,
        exit_code=run.exit_code,
        stdout=stdout,
        log_path=str(log_path),
    )
