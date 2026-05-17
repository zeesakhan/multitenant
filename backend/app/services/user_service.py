from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
from app.models.user import User, Role, Permission
from app.schemas.user import UserCreate, UserUpdate, UserRoleAssign
from app.constants.enums import UserStatus
from app.constants.messages import USER_NOT_FOUND, USER_EMAIL_TAKEN, AUTH_INVALID_CREDENTIALS, AUTH_USER_INACTIVE
from app.utils.jwt_handler import encode as jwt_encode
from config import get_settings
from typing import List, Optional
import uuid

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(payload: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt_encode({**payload, "exp": expire.timestamp(), "type": "access"}, settings.secret_key)


def create_refresh_token(payload: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return jwt_encode({**payload, "exp": expire.timestamp(), "type": "refresh"}, settings.secret_key)


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate(self, tenant_id: str, email: str, password: str) -> User:
        user = self.db.query(User).filter(
            User.tenant_id == tenant_id, User.email == email.lower()
        ).first()

        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=AUTH_INVALID_CREDENTIALS)

        if user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_USER_INACTIVE)

        user.last_login = datetime.now(timezone.utc)
        user.failed_login_count = 0
        self.db.commit()
        return user

    def generate_tokens(self, user: User) -> dict:
        payload = {"sub": user.id, "tenant_id": user.tenant_id, "email": user.email, "user_type": user.user_type}
        return {
            "access_token": create_access_token(payload),
            "refresh_token": create_refresh_token({"sub": user.id, "tenant_id": user.tenant_id}),
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }

    def create(self, tenant_id: str, data: UserCreate) -> User:
        if self.db.query(User).filter(User.tenant_id == tenant_id, User.email == data.email.lower()).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=USER_EMAIL_TAKEN)

        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            user_type=data.user_type,
            status=UserStatus.ACTIVE,
        )
        if data.role_ids:
            user.roles = self.db.query(Role).filter(Role.id.in_(data.role_ids), Role.tenant_id == tenant_id).all()

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, tenant_id: str, user_id: str) -> User:
        user = self.db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=USER_NOT_FOUND)
        return user

    def list_users(self, tenant_id: str, skip: int = 0, limit: int = 20) -> tuple[List[User], int]:
        q = self.db.query(User).filter(User.tenant_id == tenant_id)
        return q.offset(skip).limit(limit).all(), q.count()

    def update(self, tenant_id: str, user_id: str, data: UserUpdate) -> User:
        user = self.get_by_id(tenant_id, user_id)
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(user, k, v)
        self.db.commit()
        self.db.refresh(user)
        return user

    def assign_roles(self, tenant_id: str, user_id: str, data: UserRoleAssign) -> User:
        user = self.get_by_id(tenant_id, user_id)
        user.roles = self.db.query(Role).filter(Role.id.in_(data.role_ids), Role.tenant_id == tenant_id).all()
        self.db.commit()
        self.db.refresh(user)
        return user

    def deactivate(self, tenant_id: str, user_id: str) -> User:
        user = self.get_by_id(tenant_id, user_id)
        user.status = UserStatus.INACTIVE
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_role(self, tenant_id: str, name: str, description: str = None, permission_ids: List[str] = None) -> Role:
        role = Role(id=str(uuid.uuid4()), tenant_id=tenant_id, name=name, description=description)
        if permission_ids:
            role.permissions = self.db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def list_roles(self, tenant_id: str) -> List[Role]:
        return self.db.query(Role).filter(Role.tenant_id == tenant_id).all()

    def get_role(self, tenant_id: str, role_id: str) -> Role:
        role = self.db.query(Role).filter(Role.id == role_id, Role.tenant_id == tenant_id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
        return role

    def list_permissions(self) -> List[Permission]:
        return self.db.query(Permission).all()
