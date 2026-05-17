from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.payment import Payment
from app.models.policy import Policy
from app.schemas.payment import PaymentCreate
from app.constants.enums import PaymentStatus, PolicyStatus
from app.utils.formatters import generate_reference_number
from app.services.audit_service import AuditService
from datetime import datetime, timezone
import uuid


class PaymentService:
    def __init__(self, db: Session, audit_service: AuditService):
        self.db = db
        self.audit = audit_service

    def record_payment(self, tenant_id: str, policy_id: str, data: PaymentCreate, user_id: str) -> Payment:
        policy = self.db.query(Policy).filter(
            and_(Policy.tenant_id == tenant_id, Policy.id == policy_id)
        ).first()
        if not policy:
            raise ValueError("Policy not found")
        if policy.status not in (PolicyStatus.ACTIVE,):
            raise ValueError(f"Cannot record payment for a {policy.status} policy")

        payment = Payment(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            payment_number=generate_reference_number("PAY"),
            policy_id=policy_id,
            amount=data.amount,
            status=PaymentStatus.SUCCESS,
            method=data.method,
            reference=data.reference,
            notes=data.notes,
            paid_at=data.paid_at or datetime.now(timezone.utc),
        )
        self.db.add(payment)
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="create",
            entity_type="payment",
            entity_id=payment.id,
            user_id=user_id,
            new_values={"amount": str(data.amount), "policy_id": policy_id},
        )
        return payment

    def list_by_policy(self, tenant_id: str, policy_id: str) -> list[Payment]:
        return (
            self.db.query(Payment)
            .filter(and_(Payment.tenant_id == tenant_id, Payment.policy_id == policy_id))
            .order_by(Payment.paid_at.desc())
            .all()
        )

    def list_all(self, tenant_id: str, skip: int = 0, limit: int = 20) -> "tuple[list, int]":
        q = self.db.query(Payment).filter(Payment.tenant_id == tenant_id)
        total = q.count()
        items = q.order_by(Payment.paid_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def total_collected(self, tenant_id: str) -> float:
        result = (
            self.db.query(func.sum(Payment.amount))
            .filter(
                and_(
                    Payment.tenant_id == tenant_id,
                    Payment.status == PaymentStatus.SUCCESS,
                )
            )
            .scalar()
        )
        return float(result or 0)
