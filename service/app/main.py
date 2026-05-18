from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.login import router as login_router
from app.api.targets import router as targets_router
from app.auth import get_current_user, seed_admin_user
from app.database import SessionLocal, get_db
from app.models import User


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    with SessionLocal() as db:
        seed_admin_user(db)
    yield


app = FastAPI(title="Ansible Roller", lifespan=lifespan)
app.include_router(login_router)
app.include_router(targets_router)


@app.get("/healthz", response_model=None)
def healthz(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "error"},
        )
    return {"status": "ok", "database": "ok"}


@app.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username}
