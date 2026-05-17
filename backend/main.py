from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException

from config import get_settings
from app.utils.logger import configure_logging
from app.middleware.tenant_context import TenantContextMiddleware
from app.middleware.audit_logger import AuditLoggerMiddleware
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.api.v1 import v1_router
from app.api.health import router as health_router

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.utils.logger import get_logger
    logger = get_logger("startup")
    logger.info("Health Insurance Platform started", version=settings.app_version)

    if "sqlite" in settings.database_url:
        _bootstrap_sqlite_dev()

    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Custom middleware (order matters: first added = outermost)
app.add_middleware(AuditLoggerMiddleware)
app.add_middleware(TenantContextMiddleware)

# Exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Routers
app.include_router(health_router)
app.include_router(v1_router)


def _bootstrap_sqlite_dev():
    """Create tables and seed demo data for local SQLite dev mode."""
    from app.models.base import Base
    from app.db.database import _get_engine, _get_session_factory
    import app.models  # ensure all models are registered
    import app.models.application  # noqa: F401
    import app.models.policy       # noqa: F401
    import app.models.member       # noqa: F401
    import app.models.payment      # noqa: F401
    import app.models.claim        # noqa: F401
    from app.models import product  # noqa: F401

    engine = _get_engine()
    Base.metadata.create_all(bind=engine)

    from app.models.tenant import Tenant, BrandConfig
    from app.models.user import User
    from app.constants.enums import TenantStatus, UserType, UserStatus
    from app.services.user_service import hash_password
    import uuid

    factory = _get_session_factory()
    db = factory()
    try:
        if db.query(Tenant).filter(Tenant.code == "TESTCO").first():
            return  # already seeded

        tenant = Tenant(
            id=str(uuid.uuid4()),
            code="TESTCO",
            name="Test Insurance Co",
            status=TenantStatus.ACTIVE,
            currency="USD",
            timezone="UTC",
            config={},
        )
        db.add(tenant)
        db.flush()

        db.add(BrandConfig(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            company_name="Test Insurance Co",
        ))

        db.add(User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email="admin@testco.com",
            password_hash=hash_password("admin123"),
            first_name="Admin",
            last_name="User",
            user_type=UserType.TENANT_ADMIN,
            status=UserStatus.ACTIVE,
        ))

        db.add(User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email="agent@testco.com",
            password_hash=hash_password("password123"),
            first_name="John",
            last_name="Agent",
            user_type=UserType.AGENT,
            status=UserStatus.ACTIVE,
        ))

        # Super admin tenant + user (needed for tenant management)
        sys_tenant = Tenant(
            id=str(uuid.uuid4()),
            code="SYSTEM",
            name="System",
            status=TenantStatus.ACTIVE,
            currency="USD",
            timezone="UTC",
            config={},
        )
        db.add(sys_tenant)
        db.flush()
        db.add(BrandConfig(
            id=str(uuid.uuid4()),
            tenant_id=sys_tenant.id,
            company_name="System",
        ))
        db.add(User(
            id=str(uuid.uuid4()),
            tenant_id=sys_tenant.id,
            email="superadmin@system.com",
            password_hash=hash_password("super123"),
            first_name="Super",
            last_name="Admin",
            user_type=UserType.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
        ))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
