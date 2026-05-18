from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.policy import Policy
from app.models.member import Member
from app.models.payment import Payment
from app.models.claim import Claim
from app.models.document import DocumentUpload
from app.constants.enums import UserType, UserStatus, ClaimType, ClaimStatus
from app.services.user_service import UserService, hash_password, verify_password
from app.utils.formatters import api_response, generate_reference_number
from config import get_settings
from pydantic import BaseModel
from typing import Optional
from datetime import date
import uuid

settings = get_settings()
router = APIRouter(prefix="/customer", tags=["Customer Portal"])


# ── Dependencies ──────────────────────────────────────────────────────────────

def get_current_customer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.user_type != UserType.CUSTOMER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer portal access only.")
    return current_user


def get_customer_policy(
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> Policy:
    policy_id = (current_user.extra_data or {}).get("policy_id")
    if not policy_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No policy linked to this account.")
    policy = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.tenant_id == current_user.tenant_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")
    return policy


# ── Schemas ───────────────────────────────────────────────────────────────────

class CustomerRegister(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    policy_number: str
    date_of_birth: date


class CustomerProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class CustomerPasswordChange(BaseModel):
    current_password: str
    new_password: str


class CustomerClaimCreate(BaseModel):
    claim_type: str
    incident_date: date
    description: str
    claimed_amount: float
    member_id: Optional[str] = None


# ── Registration ──────────────────────────────────────────────────────────────

@router.post("/register", response_model=dict)
def register(payload: CustomerRegister, request: Request, db: Session = Depends(get_db)):
    """Self-registration: link an email/password account to a policy via policy number + DOB."""
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant context required.")

    policy = db.query(Policy).filter(
        Policy.tenant_id == tenant_id,
        Policy.policy_number == payload.policy_number.upper().strip(),
    ).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found. Check your policy number.")

    # Verify DOB matches primary (self) member on the linked application
    verified = False
    if policy.application_id:
        primary = (
            db.query(Member)
            .filter(
                Member.application_id == policy.application_id,
                Member.relationship == "self",
            )
            .first()
        )
        if primary and str(primary.date_of_birth) == str(payload.date_of_birth):
            verified = True

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identity verification failed. Check your date of birth and policy number.",
        )

    if db.query(User).filter(User.tenant_id == tenant_id, User.email == payload.email.lower()).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    # Each policy can only have one customer portal account
    for u in db.query(User).filter(User.tenant_id == tenant_id, User.user_type == UserType.CUSTOMER).all():
        if (u.extra_data or {}).get("policy_id") == policy.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This policy already has a customer portal account.")

    user = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        user_type=UserType.CUSTOMER,
        status=UserStatus.ACTIVE,
        extra_data={"policy_id": policy.id},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    tokens = UserService(db).generate_tokens(user)
    return api_response(data=tokens, message="Account created. Welcome to your policy portal!")


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/me", response_model=dict)
def get_profile(current_user: User = Depends(get_current_customer)):
    return api_response(data={
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "phone": current_user.phone,
        "user_type": current_user.user_type,
        "policy_id": (current_user.extra_data or {}).get("policy_id"),
    })


@router.put("/me", response_model=dict)
def update_profile(
    payload: CustomerProfileUpdate,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(current_user, k, v)
    db.commit()
    return api_response(message="Profile updated.")


@router.put("/me/password", response_model=dict)
def change_password(
    payload: CustomerPasswordChange,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password must be at least 8 characters.")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return api_response(message="Password changed successfully.")


# ── Policy ────────────────────────────────────────────────────────────────────

@router.get("/policy", response_model=dict)
def get_policy_detail(
    current_user: User = Depends(get_current_customer),
    policy: Policy = Depends(get_customer_policy),
):
    return api_response(data={
        "id": policy.id,
        "policy_number": policy.policy_number,
        "status": policy.status,
        "customer_name": policy.customer_name,
        "customer_email": policy.customer_email,
        "product_id": policy.product_id,
        "product_name": policy.product.name if policy.product else None,
        "plan_id": policy.plan_id,
        "plan_name": policy.plan.name if policy.plan else None,
        "plan_type": policy.plan.plan_type if policy.plan else None,
        "base_premium": str(policy.plan.base_premium) if policy.plan else None,
        "total_premium": str(policy.total_premium),
        "member_count": policy.member_count,
        "effective_date": policy.effective_date.isoformat() if policy.effective_date else None,
        "expiry_date": policy.expiry_date.isoformat() if policy.expiry_date else None,
        "issued_at": policy.issued_at.isoformat() if policy.issued_at else None,
    })


@router.get("/coverage", response_model=dict)
def get_coverage(
    policy: Policy = Depends(get_customer_policy),
    db: Session = Depends(get_db),
):
    from app.models.application import ApplicationItem
    items = []
    if policy.application_id:
        for item in db.query(ApplicationItem).filter(ApplicationItem.application_id == policy.application_id).all():
            cov = item.coverage
            items.append({
                "id": item.id,
                "coverage_name": cov.name if cov else None,
                "coverage_type": cov.coverage_type if cov else None,
                "limit_amount": str(cov.limit_amount) if cov and cov.limit_amount else None,
                "copay": str(cov.copay) if cov and cov.copay else None,
                "coinsurance_percent": str(cov.coinsurance_percent) if cov and cov.coinsurance_percent else None,
                "premium": str(item.premium),
                "status": item.status,
            })
    return api_response(data=items)


# ── Members ───────────────────────────────────────────────────────────────────

@router.get("/members", response_model=dict)
def get_members(
    policy: Policy = Depends(get_customer_policy),
    db: Session = Depends(get_db),
):
    members = []
    if policy.application_id:
        for m in db.query(Member).filter(Member.application_id == policy.application_id).all():
            members.append({
                "id": m.id,
                "first_name": m.first_name,
                "last_name": m.last_name,
                "date_of_birth": str(m.date_of_birth),
                "relationship": m.relationship,
                "gender": m.gender,
                "status": m.status,
                "email": m.email,
                "phone": m.phone,
            })
    return api_response(data=members)


# ── Payments ──────────────────────────────────────────────────────────────────

@router.get("/payments", response_model=dict)
def get_payments(
    policy: Policy = Depends(get_customer_policy),
    db: Session = Depends(get_db),
):
    payments = db.query(Payment).filter(Payment.policy_id == policy.id).order_by(Payment.paid_at.desc()).all()
    total_paid = sum(float(p.amount) for p in payments if p.status == "success")
    return api_response(data={
        "total_paid": total_paid,
        "payments": [{
            "id": p.id,
            "payment_number": p.payment_number,
            "amount": str(p.amount),
            "method": p.method,
            "status": p.status,
            "reference": p.reference,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
        } for p in payments],
    })


# ── Claims ────────────────────────────────────────────────────────────────────

@router.get("/claims", response_model=dict)
def get_claims(
    policy: Policy = Depends(get_customer_policy),
    db: Session = Depends(get_db),
):
    claims = db.query(Claim).filter(Claim.policy_id == policy.id).order_by(Claim.created_at.desc()).all()
    return api_response(data=[{
        "id": c.id,
        "claim_number": c.claim_number,
        "claim_type": c.claim_type,
        "status": c.status,
        "incident_date": str(c.incident_date) if c.incident_date else None,
        "description": c.description,
        "claimed_amount": str(c.claimed_amount),
        "approved_amount": str(c.approved_amount) if c.approved_amount else None,
        "rejection_reason": c.rejection_reason,
        "created_at": c.created_at.isoformat(),
    } for c in claims])


@router.post("/claims", response_model=dict, status_code=status.HTTP_201_CREATED)
def file_claim(
    payload: CustomerClaimCreate,
    current_user: User = Depends(get_current_customer),
    policy: Policy = Depends(get_customer_policy),
    db: Session = Depends(get_db),
):
    try:
        claim_type = ClaimType(payload.claim_type)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim type.")

    claim = Claim(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        claim_number=generate_reference_number("CLM"),
        policy_id=policy.id,
        member_id=payload.member_id,
        claim_type=claim_type,
        status=ClaimStatus.SUBMITTED,
        incident_date=payload.incident_date,
        description=payload.description,
        claimed_amount=payload.claimed_amount,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return api_response(data={
        "id": claim.id,
        "claim_number": claim.claim_number,
        "status": claim.status,
    }, message="Claim submitted successfully.")


# ── Documents ─────────────────────────────────────────────────────────────────

@router.get("/documents", response_model=dict)
def get_documents(
    policy: Policy = Depends(get_customer_policy),
    db: Session = Depends(get_db),
):
    docs = (
        db.query(DocumentUpload)
        .filter(
            DocumentUpload.entity_type == "policy",
            DocumentUpload.entity_id == policy.id,
            DocumentUpload.tenant_id == policy.tenant_id,
        )
        .order_by(DocumentUpload.created_at.desc())
        .all()
    )
    return api_response(data=[{
        "id": d.id,
        "document_type": d.document_type,
        "file_name": d.file_name,
        "mime_type": d.mime_type,
        "file_size": d.file_size,
        "validation_status": d.validation_status,
        "created_at": d.created_at.isoformat(),
    } for d in docs])
