from sqlalchemy import Column, String, Enum, JSON, Boolean, DateTime, Table, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import TenantModel, Base
from app.constants.enums import UserType, UserStatus
from datetime import datetime
from typing import Optional, List


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resource: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class Role(TenantModel):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
    )


class User(TenantModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_type: Mapped[str] = mapped_column(
        Enum(UserType, name="user_type_enum", values_callable=lambda x: [e.value for e in x]),
        default=UserType.AGENT,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(UserStatus, name="user_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=UserStatus.ACTIVE,
        nullable=False,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    tenant = relationship("Tenant", back_populates="users", foreign_keys="User.tenant_id")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def get_permission_codes(self) -> set:
        from app.constants.permissions import ROLE_PERMISSIONS
        from app.constants.enums import UserType

        codes = set()

        # Add role-based permissions
        for role in self.roles:
            for perm in role.permissions:
                codes.add(perm.code)

        # Add user_type default permissions if no roles assigned
        if not self.roles:
            user_type_key = self.user_type.lower() if isinstance(self.user_type, str) else self.user_type.value
            default_perms = ROLE_PERMISSIONS.get(user_type_key, [])
            codes.update(default_perms)

        return codes

    def has_permission(self, permission_code: str) -> bool:
        return permission_code in self.get_permission_codes()
