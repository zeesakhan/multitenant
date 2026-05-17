from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.policy import Policy
from app.models.application import Application
from app.models.product import Quote
from app.schemas.policy import PolicyRead
from app.constants.enums import ApplicationStatus, PolicyStatus
from app.utils.formatters import generate_reference_number
from app.services.audit_service import AuditService
from app.services.email_service import EmailService
from datetime import datetime, timezone, timedelta
import uuid


class PolicyService:
    def __init__(self, db: Session, audit_service: AuditService):
        self.db = db
        self.audit = audit_service

    def issue_policy(self, tenant_id: str, application_id: str, user_id: str) -> Policy:
        application = self.db.query(Application).filter(
            and_(Application.tenant_id == tenant_id, Application.id == application_id)
        ).first()

        if not application:
            raise ValueError(f"Application {application_id} not found")

        if application.status != ApplicationStatus.APPROVED:
            raise ValueError(f"Can only issue a policy for an approved application (current status: {application.status})")

        existing = self.db.query(Policy).filter(
            and_(Policy.tenant_id == tenant_id, Policy.application_id == application_id)
        ).first()
        if existing:
            raise ValueError(f"A policy has already been issued for this application: {existing.policy_number}")

        # Resolve plan_id — from application directly or from linked quote
        plan_id = application.plan_id
        product_id = application.product_id
        if not plan_id and application.quote_id:
            quote = self.db.query(Quote).filter(Quote.id == application.quote_id).first()
            if quote:
                plan_id = quote.plan_id
                product_id = quote.product_id

        if not plan_id or not product_id:
            raise ValueError("Cannot issue policy: application has no linked plan. Convert from a quote or select a plan when creating.")

        now = datetime.now(timezone.utc)
        effective_date = now
        expiry_date = now + timedelta(days=365)
        policy_number = generate_reference_number("POL")

        policy = Policy(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            policy_number=policy_number,
            application_id=application_id,
            quote_id=application.quote_id,
            product_id=product_id,
            plan_id=plan_id,
            customer_name=application.customer_name,
            customer_email=application.customer_email,
            member_count=application.member_count,
            total_premium=application.total_premium,
            status=PolicyStatus.ACTIVE,
            effective_date=effective_date,
            expiry_date=expiry_date,
            issued_by=user_id,
            issued_at=now,
        )

        self.db.add(policy)

        application.status = ApplicationStatus.ISSUED
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="issue",
            entity_type="policy",
            entity_id=policy.id,
            user_id=user_id,
            new_values={"policy_number": policy_number, "application_id": application_id},
        )

        EmailService().notify_policy_issued(
            customer_email=policy.customer_email,
            customer_name=policy.customer_name,
            policy_number=policy_number,
            effective_date=effective_date.strftime("%B %d, %Y"),
            expiry_date=expiry_date.strftime("%B %d, %Y"),
            premium=str(policy.total_premium),
        )

        return policy

    def get_by_id(self, tenant_id: str, policy_id: str) -> Policy:
        return self.db.query(Policy).filter(
            and_(Policy.tenant_id == tenant_id, Policy.id == policy_id)
        ).first()

    def get_by_application(self, tenant_id: str, application_id: str) -> Policy:
        return self.db.query(Policy).filter(
            and_(Policy.tenant_id == tenant_id, Policy.application_id == application_id)
        ).first()

    def renew(self, tenant_id: str, policy_id: str, user_id: str) -> Policy:
        policy = self.get_by_id(tenant_id, policy_id)
        if not policy:
            raise ValueError("Policy not found")
        if policy.status not in (PolicyStatus.ACTIVE, "expired"):
            raise ValueError(f"Can only renew an active or expired policy (current: {policy.status})")

        now = datetime.now(timezone.utc)
        expiry = policy.expiry_date
        if expiry.tzinfo is None:
            from datetime import timezone as tz
            expiry = expiry.replace(tzinfo=tz.utc)
        new_effective = expiry if expiry > now else now
        new_expiry = new_effective + timedelta(days=365)
        new_number = generate_reference_number("POL")

        renewed = Policy(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            policy_number=new_number,
            application_id=None,
            quote_id=policy.quote_id,
            product_id=policy.product_id,
            plan_id=policy.plan_id,
            customer_name=policy.customer_name,
            customer_email=policy.customer_email,
            member_count=policy.member_count,
            total_premium=policy.total_premium,
            status=PolicyStatus.ACTIVE,
            effective_date=new_effective,
            expiry_date=new_expiry,
            issued_by=user_id,
            issued_at=now,
        )
        self.db.add(renewed)

        # Mark original as renewed
        policy.status = "renewed"
        self.db.flush()

        self.audit.log(tenant_id=tenant_id, action="renew", entity_type="policy",
                       entity_id=renewed.id, user_id=user_id,
                       new_values={"policy_number": new_number, "original_id": policy_id})

        EmailService().notify_policy_renewal(
            customer_email=renewed.customer_email,
            customer_name=renewed.customer_name,
            old_number=policy.policy_number,
            new_number=new_number,
            expiry_date=new_expiry.strftime("%B %d, %Y"),
        )

        return renewed

    def list_policies(self, tenant_id: str, skip: int = 0, limit: int = 20) -> "tuple[list, int]":
        query = self.db.query(Policy).filter(Policy.tenant_id == tenant_id)
        total = query.count()
        policies = query.order_by(Policy.created_at.desc()).offset(skip).limit(limit).all()
        return policies, total
