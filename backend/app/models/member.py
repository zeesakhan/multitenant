from sqlalchemy import String, Enum, Date, Index, ForeignKey, JSON, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship as sa_relationship
from app.models.base import TenantModel
from app.constants.enums import MemberRelationship, MemberStatus, Gender
from datetime import date
from typing import Optional
from decimal import Decimal


class Member(TenantModel):
    __tablename__ = "members"

    application_id: Mapped[str] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    relationship: Mapped[str] = mapped_column(
        Enum(MemberRelationship, name="member_relationship_enum", values_callable=lambda x: [e.value for e in x]), nullable=False
    )
    gender: Mapped[str] = mapped_column(
        Enum(Gender, name="gender_enum", values_callable=lambda x: [e.value for e in x]), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(MemberStatus, name="member_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=MemberStatus.ACTIVE,
        nullable=False,
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    national_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # UAE-specific compliance fields
    passport_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    emirates_id: Mapped[Optional[str]] = mapped_column(String(25), nullable=True)
    nationality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    visa_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    document_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    place_of_birth: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Medical questionnaire fields (migration 0020)
    medical_questionnaire: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    pregnancy_questionnaire: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    height_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    marital_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    application = sa_relationship("Application", back_populates="members")

    __table_args__ = (
        Index("ix_members_application", "application_id"),
        Index("ix_members_tenant", "tenant_id"),
    )
