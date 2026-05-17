from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.member import Member
from app.models.application import Application
from app.schemas.member import MemberCreate, MemberUpdate
from app.constants.enums import ApplicationStatus, MemberStatus
from app.services.audit_service import AuditService
import uuid


class MemberService:
    def __init__(self, db: Session, audit_service: AuditService):
        self.db = db
        self.audit = audit_service

    def _get_application(self, tenant_id: str, application_id: str) -> Application:
        app = self.db.query(Application).filter(
            and_(Application.tenant_id == tenant_id, Application.id == application_id)
        ).first()
        if not app:
            raise ValueError(f"Application {application_id} not found")
        return app

    def add_member(self, tenant_id: str, application_id: str, data: MemberCreate, user_id: str) -> Member:
        app = self._get_application(tenant_id, application_id)
        if app.status != ApplicationStatus.DRAFT:
            raise ValueError(f"Can only add members to a DRAFT application (current: {app.status})")

        member = Member(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            application_id=application_id,
            first_name=data.first_name,
            last_name=data.last_name,
            date_of_birth=data.date_of_birth,
            relationship=data.relationship,
            gender=data.gender,
            status=MemberStatus.ACTIVE,
            email=data.email,
            phone=data.phone,
            national_id=data.national_id,
        )
        self.db.add(member)
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="create",
            entity_type="member",
            entity_id=member.id,
            user_id=user_id,
        )
        return member

    def list_all(self, tenant_id: str, skip: int = 0, limit: int = 20) -> "tuple[list, int]":
        query = self.db.query(Member).filter(Member.tenant_id == tenant_id)
        total = query.count()
        members = query.order_by(Member.created_at.desc()).offset(skip).limit(limit).all()
        return members, total

    def list_members(self, tenant_id: str, application_id: str) -> list[Member]:
        return self.db.query(Member).filter(
            and_(Member.tenant_id == tenant_id, Member.application_id == application_id)
        ).order_by(Member.created_at).all()

    def get_by_id(self, tenant_id: str, member_id: str) -> Member:
        return self.db.query(Member).filter(
            and_(Member.tenant_id == tenant_id, Member.id == member_id)
        ).first()

    def update_member(self, tenant_id: str, member_id: str, data: MemberUpdate, user_id: str) -> Member:
        member = self.get_by_id(tenant_id, member_id)
        if not member:
            raise ValueError(f"Member {member_id} not found")

        app = self._get_application(tenant_id, member.application_id)
        if app.status != ApplicationStatus.DRAFT:
            raise ValueError(f"Can only update members on a DRAFT application (current: {app.status})")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(member, field, value)
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="update",
            entity_type="member",
            entity_id=member_id,
            user_id=user_id,
        )
        return member

    def remove_member(self, tenant_id: str, member_id: str, user_id: str) -> bool:
        member = self.get_by_id(tenant_id, member_id)
        if not member:
            return False

        app = self._get_application(tenant_id, member.application_id)
        if app.status != ApplicationStatus.DRAFT:
            raise ValueError(f"Can only remove members from a DRAFT application (current: {app.status})")

        self.db.delete(member)
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="delete",
            entity_type="member",
            entity_id=member_id,
            user_id=user_id,
        )
        return True
