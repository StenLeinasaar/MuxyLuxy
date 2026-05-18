from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ansible.validation import RoleValidationError, validate_role_path
from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Role

router = APIRouter(
    prefix="/roles",
    dependencies=[Depends(get_current_user)],
)


class RolePayload(BaseModel):
    path: str = Field(min_length=1)
    description: str | None = None


class RoleResponse(BaseModel):
    name: str
    description: str | None
    path: str
    enabled: bool


def _role_response(role: Role) -> RoleResponse:
    return RoleResponse(
        name=role.name,
        description=role.description,
        path=role.path,
        enabled=role.enabled,
    )


@router.get("", response_model=list[RoleResponse])
def list_roles(db: Session = Depends(get_db)) -> list[RoleResponse]:
    roles = db.scalars(select(Role).order_by(Role.name)).all()
    return [_role_response(role) for role in roles]


@router.put("/{role_name}", response_model=RoleResponse)
def upsert_role(
    payload: RolePayload,
    role_name: str = Path(min_length=1),
    db: Session = Depends(get_db),
) -> RoleResponse:
    try:
        role_path = validate_role_path(
            role_name=role_name,
            role_path=payload.path,
            roles_root=settings.ansible_roles_path,
        )
    except RoleValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    role = db.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        role = Role(
            name=role_name,
            description=payload.description,
            path=role_path,
            enabled=True,
        )
        db.add(role)
    else:
        role.description = payload.description
        role.path = role_path
        role.enabled = True

    db.commit()
    db.refresh(role)
    return _role_response(role)


@router.delete("/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_name: str = Path(min_length=1),
    db: Session = Depends(get_db),
) -> Response:
    role = db.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    role.enabled = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
