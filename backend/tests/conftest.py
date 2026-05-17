import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from main import app
from app.models.base import Base
from app.models import Tenant, BrandConfig, User, Role, Permission
from app.db.database import get_sync_session
from app.constants.enums import TenantStatus, UserType, UserStatus

TEST_DATABASE_URL = "sqlite:///./test.db"


def hash_password(password: str) -> str:
    from passlib.context import CryptContext
    return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(password)


def create_access_token(payload: dict) -> str:
    from app.utils.jwt_handler import encode as jwt_encode
    from datetime import datetime, timezone, timedelta
    from config import get_settings
    s = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=s.access_token_expire_minutes)
    return jwt_encode({**payload, "exp": expire.timestamp(), "type": "access"}, s.secret_key)


@pytest.fixture(scope="session")
def engine():
    e = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=e)
    yield e
    Base.metadata.drop_all(bind=e)


@pytest.fixture(scope="function")
def db(engine):
    """Each test gets a transaction that is rolled back on teardown."""
    connection = engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(bind=connection)
    session = TestSession()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    app.dependency_overrides[get_sync_session] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def tenant(db) -> Tenant:
    t = Tenant(
        id=str(uuid.uuid4()),
        code=f"TEST_{uuid.uuid4().hex[:6].upper()}",
        name="Test Insurance Co",
        status=TenantStatus.ACTIVE,
        currency="USD",
        timezone="UTC",
        config={},
    )
    db.add(t)
    db.flush()
    brand = BrandConfig(id=str(uuid.uuid4()), tenant_id=t.id, company_name="Test Co")
    db.add(brand)
    db.flush()
    return t


@pytest.fixture
def tenant2(db) -> Tenant:
    t = Tenant(
        id=str(uuid.uuid4()),
        code=f"OTHER_{uuid.uuid4().hex[:6].upper()}",
        name="Other Insurance Co",
        status=TenantStatus.ACTIVE,
        currency="USD",
        timezone="UTC",
        config={},
    )
    db.add(t)
    db.flush()
    brand = BrandConfig(id=str(uuid.uuid4()), tenant_id=t.id, company_name="Other Co")
    db.add(brand)
    db.flush()
    return t


@pytest.fixture
def user(db, tenant) -> User:
    u = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        email="agent@testco.com",
        password_hash=hash_password("password123"),
        first_name="John",
        last_name="Agent",
        user_type=UserType.AGENT,
        status=UserStatus.ACTIVE,
    )
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def admin_user(db, tenant) -> User:
    u = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        email="admin@testco.com",
        password_hash=hash_password("admin123"),
        first_name="Admin",
        last_name="User",
        user_type=UserType.TENANT_ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def super_admin(db) -> User:
    t = Tenant(
        id=str(uuid.uuid4()),
        code=f"SYS_{uuid.uuid4().hex[:6].upper()}",
        name="System",
        status=TenantStatus.ACTIVE,
        currency="USD",
        timezone="UTC",
        config={},
    )
    db.add(t)
    db.flush()
    u = User(
        id=str(uuid.uuid4()),
        tenant_id=t.id,
        email="superadmin@system.com",
        password_hash=hash_password("super123"),
        first_name="Super",
        last_name="Admin",
        user_type=UserType.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def auth_headers(user, tenant) -> dict:
    token = create_access_token({
        "sub": user.id, "tenant_id": tenant.id,
        "email": user.email, "user_type": user.user_type,
    })
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant.id}


@pytest.fixture
def admin_headers(admin_user, tenant) -> dict:
    token = create_access_token({
        "sub": admin_user.id, "tenant_id": tenant.id,
        "email": admin_user.email, "user_type": admin_user.user_type,
    })
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant.id}


@pytest.fixture
def super_admin_headers(super_admin) -> dict:
    token = create_access_token({
        "sub": super_admin.id, "tenant_id": super_admin.tenant_id,
        "email": super_admin.email, "user_type": super_admin.user_type,
    })
    return {"Authorization": f"Bearer {token}"}
