from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Target

router = APIRouter(
    prefix="/targets",
    dependencies=[Depends(get_current_user)],
)


class TargetPayload(BaseModel):
    host: str = Field(min_length=1)
    port: int = 22
    username: str = Field(min_length=1)
    auth_type: Literal["ssh_key"]
    ssh_private_key_path: str = Field(min_length=1)
    python_interpreter: str = "/usr/bin/python3"


class TargetResponse(BaseModel):
    name: str
    host: str
    port: int
    username: str
    auth_type: str
    ssh_private_key_path: str
    python_interpreter: str


def _target_response(target: Target) -> TargetResponse:
    return TargetResponse(
        name=target.name,
        host=target.host,
        port=target.port,
        username=target.username,
        auth_type=target.auth_type,
        ssh_private_key_path=target.ssh_private_key_path or "",
        python_interpreter=target.python_interpreter or "/usr/bin/python3",
    )


@router.get("", response_model=list[TargetResponse])
def list_targets(db: Session = Depends(get_db)) -> list[TargetResponse]:
    targets = db.scalars(select(Target).order_by(Target.name)).all()
    return [_target_response(target) for target in targets]


@router.put("/{target_name}", response_model=TargetResponse)
def upsert_target(
    payload: TargetPayload,
    target_name: str = Path(min_length=1),
    db: Session = Depends(get_db),
) -> TargetResponse:
    target = db.scalar(select(Target).where(Target.name == target_name))
    if target is None:
        target = Target(name=target_name, **payload.model_dump())
        db.add(target)
    else:
        for field, value in payload.model_dump().items():
            setattr(target, field, value)

    db.commit()
    db.refresh(target)
    return _target_response(target)


@router.delete("/{target_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(
    target_name: str = Path(min_length=1),
    db: Session = Depends(get_db),
) -> Response:
    target = db.scalar(select(Target).where(Target.name == target_name))
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    db.delete(target)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
