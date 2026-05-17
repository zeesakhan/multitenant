from sqlalchemy import String, Enum, Date, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship
from app.models.base import TenantModel
from app.constants.enums import MemberRelationship, MemberStatus, Gender
from datetime import date
from typing import Optional


class Member(TenantModel):
    __tablename__ = "members"

    application_id: Mapped[str] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    relationship: Mapped[str] = mapped_column(
        Enum(MemberRelationship, name="member_relationship_enum"), nullable=False
    )
    gender: Mapped[str] = mapped_column(
        Enum(Gender, name="gender_enum"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(MemberStatus, name="member_status_enum"),
        default=MemberStatus.ACTIVE,
        nullable=False,
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    national_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    application = sa_relationship("Application", back_populates="members")

    __table_args__ = (
        Index("ix_members_application", "application_id"),
        Index("ix_members_tenant", "tenant_id"),
    )
