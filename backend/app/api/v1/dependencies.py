from fastapi import Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_sync_session
from app.middleware.auth import get_current_user, require_permissions, require_super_admin
from app.schemas.base import PaginationParams


def get_db(db: Session = Depends(get_sync_session)) -> Session:
    return db


def get_pagination(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(page=page, per_page=per_page)


__all__ = [
    "get_db",
    "get_sync_session",
    "get_current_user",
    "require_permissions",
    "require_super_admin",
    "get_pagination",
]
