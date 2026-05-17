from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, StaticPool
from config import get_settings

settings = get_settings()

_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        kwargs = dict(
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            echo=settings.database_echo,
        )
        _engine = create_engine(settings.database_url, **kwargs)
    return _engine


def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=_get_engine(),
            class_=Session,
            expire_on_commit=False,
        )
    return _SessionLocal


def get_sync_session():
    """FastAPI dependency — yields a DB session per request."""
    factory = _get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()
