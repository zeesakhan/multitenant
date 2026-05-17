from dataclasses import dataclass
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_sync_session
from app.models.user import User
from app.models.tenant import Tenant
from app.constants.enums import UserStatus, TenantStatus
from app.constants.messages import (
    AUTH_TOKEN_INVALID, AUTH_TOKEN_EXPIRED,
    AUTH_USER_INACTIVE, AUTH_TENANT_INACTIVE,
    AUTH_INSUFFICIENT_PERMISSIONS,
)
from app.utils.jwt_handler import decode, JWTDecodeError, JWTExpiredError
from config import get_settings


@dataclass
class AuthContext:
    """Holds both user and tenant so callers can use .tenant_id or .id (tenant alias)."""
    user: User
    tenant: Tenant

    @property
    def id(self) -> str:
        return self.tenant.id

    @property
    def tenant_id(self) -> str:
        return self.tenant.id

settings = get_settings()
security = HTTPBearer()


def decode_token(token: str) -> dict:
    try:
        return decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTExpiredError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=AUTH_TOKEN_EXPIRED)
    except JWTDecodeError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=AUTH_TOKEN_INVALID)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_sync_session),
) -> User:
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=AUTH_TOKEN_INVALID)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=AUTH_TOKEN_INVALID)

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_USER_INACTIVE)

    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_TENANT_INACTIVE)

    return user


def require_permissions(required):
    # Allow both single string and list of strings
    if isinstance(required, str):
        required = [required]

    def _checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_sync_session)) -> AuthContext:
        user_perms = current_user.get_permission_codes()
        missing = [p for p in required if p not in user_perms]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_INSUFFICIENT_PERMISSIONS)
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_TENANT_INACTIVE)
        return AuthContext(user=current_user, tenant=tenant)
    return _checker


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    from app.constants.enums import UserType
    if current_user.user_type != UserType.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_INSUFFICIENT_PERMISSIONS)
    return current_user
