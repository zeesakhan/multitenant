from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.claim import Claim
from app.models.policy import Policy
from app.schemas.claim import ClaimCreate, ClaimUpdate, ClaimReview
from app.constants.enums import ClaimStatus, PolicyStatus
from app.utils.formatters import generate_reference_number
from app.services.audit_service import AuditService
from datetime import datetime, timezone
from typing import Optional, List, Tuple
import uuid


class ClaimService:
    def __init__(self, db: Session, audit_service: AuditService):
        self.db = db
        self.audit = audit_service

    def create(self, tenant_id: str, data: ClaimCreate, user_id: str) -> Claim:
        policy = self.db.query(Policy).filter(
            and_(Policy.tenant_id == tenant_id, Policy.id == data.policy_id)
        ).first()
        if not policy:
            raise ValueError("Policy not found")
        if policy.status != PolicyStatus.ACTIVE:
            raise ValueError(f"Cannot file a claim on a {policy.status} policy")

        claim = Claim(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            claim_number=generate_reference_number("CLM"),
            policy_id=data.policy_id,
            member_id=data.member_id,
            claim_type=data.claim_type,
            status=ClaimStatus.SUBMITTED,
            incident_date=data.incident_date,
            description=data.description,
            claimed_amount=data.claimed_amount,
        )
        self.db.add(claim)
        self.db.flush()
        self.audit.log(tenant_id=tenant_id, action="create", entity_type="claim",
                       entity_id=claim.id, user_id=user_id,
                       new_values={"claim_number": claim.claim_number, "policy_id": data.policy_id})
        return claim

    def get(self, tenant_id: str, claim_id: str) -> Optional[Claim]:
        return self.db.query(Claim).filter(
            and_(Claim.tenant_id == tenant_id, Claim.id == claim_id)
        ).first()

    def list_by_policy(self, tenant_id: str, policy_id: str) -> List[Claim]:
        return (
            self.db.query(Claim)
            .filter(and_(Claim.tenant_id == tenant_id, Claim.policy_id == policy_id))
            .order_by(Claim.created_at.desc())
            .all()
        )

    def list_all(self, tenant_id: str, skip: int = 0, limit: int = 20) -> Tuple[List[Claim], int]:
        q = self.db.query(Claim).filter(Claim.tenant_id == tenant_id)
        total = q.count()
        return q.order_by(Claim.created_at.desc()).offset(skip).limit(limit).all(), total

    def update(self, tenant_id: str, claim_id: str, data: ClaimUpdate, user_id: str) -> Claim:
        claim = self.get(tenant_id, claim_id)
        if not claim:
            raise ValueError("Claim not found")
        if claim.status != ClaimStatus.SUBMITTED:
            raise ValueError("Can only update a submitted claim")
        if data.description is not None:
            claim.description = data.description
        if data.claimed_amount is not None:
            claim.claimed_amount = data.claimed_amount
        self.db.flush()
        return claim

    def start_review(self, tenant_id: str, claim_id: str, user_id: str) -> Claim:
        claim = self.get(tenant_id, claim_id)
        if not claim:
            raise ValueError("Claim not found")
        if claim.status != ClaimStatus.SUBMITTED:
            raise ValueError(f"Cannot start review on a {claim.status} claim")
        claim.status = ClaimStatus.UNDER_REVIEW
        claim.reviewer_id = user_id
        self.db.flush()
        return claim

    def approve(self, tenant_id: str, claim_id: str, data: ClaimReview, user_id: str) -> Claim:
        claim = self.get(tenant_id, claim_id)
        if not claim:
            raise ValueError("Claim not found")
        if claim.status not in (ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW):
            raise ValueError(f"Cannot approve a {claim.status} claim")
        claim.status = ClaimStatus.APPROVED
        claim.approved_amount = data.approved_amount if data.approved_amount is not None else claim.claimed_amount
        claim.reviewer_id = user_id
        claim.reviewed_at = datetime.now(timezone.utc)
        self.db.flush()
        self.audit.log(tenant_id=tenant_id, action="approve", entity_type="claim",
                       entity_id=claim.id, user_id=user_id,
                       new_values={"approved_amount": str(claim.approved_amount)})
        return claim

    def reject(self, tenant_id: str, claim_id: str, reason: str, user_id: str) -> Claim:
        claim = self.get(tenant_id, claim_id)
        if not claim:
            raise ValueError("Claim not found")
        if claim.status not in (ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW):
            raise ValueError(f"Cannot reject a {claim.status} claim")
        claim.status = ClaimStatus.REJECTED
        claim.rejection_reason = reason
        claim.reviewer_id = user_id
        claim.reviewed_at = datetime.now(timezone.utc)
        self.db.flush()
        self.audit.log(tenant_id=tenant_id, action="reject", entity_type="claim",
                       entity_id=claim.id, user_id=user_id,
                       new_values={"rejection_reason": reason})
        return claim

    def mark_paid(self, tenant_id: str, claim_id: str, user_id: str) -> Claim:
        claim = self.get(tenant_id, claim_id)
        if not claim:
            raise ValueError("Claim not found")
        if claim.status != ClaimStatus.APPROVED:
            raise ValueError("Can only pay an approved claim")
        claim.status = ClaimStatus.PAID
        claim.paid_at = datetime.now(timezone.utc)
        self.db.flush()
        return claim
