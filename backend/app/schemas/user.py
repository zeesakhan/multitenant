from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime
from app.constants.enums import UserType, UserStatus


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    description: Optional[str] = None
    resource: Optional[str] = None


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permission_ids: List[str] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[str]] = None


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    is_system_role: bool
    permissions: List[PermissionRead] = []


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    user_type: UserType = UserType.AGENT
    role_ids: List[str] = []


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    user_type: Optional[UserType] = None
    status: Optional[UserStatus] = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    user_type: UserType
    status: UserStatus
    last_login: Optional[datetime] = None
    roles: List[RoleRead] = []
    created_at: datetime


class UserRoleAssign(BaseModel):
    role_ids: List[str]
