from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db
from app.models.product import Product, Plan
from app.models.application import Application, ApplicationItem
from app.models.member import Member
from app.models.tenant import Tenant
from app.constants.enums import ApplicationStatus, MemberRelationship, MemberStatus, Gender
from app.utils.formatters import api_response, generate_reference_number
from pydantic import BaseModel
from typing import Optional
from datetime import date
import uuid
from decimal import Decimal

router = APIRouter(prefix="/buy", tags=["Self-Service Purchase"])

# Per-relationship premium factors relative to base_premium
_FACTORS = {
    "self": 1.00, "spouse": 0.75, "parent": 0.70,
    "sibling": 0.65, "child": 0.35, "dependent": 0.40,
}


def _get_tenant(request: Request, db: Session = Depends(get_db)) -> Tenant:
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant context required.")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.")
    return tenant


def _calc_premium(base: float, members: list) -> tuple[float, list]:
    breakdown = []
    total = 0.0
    for m in members:
        factor = _FACTORS.get(m.relationship, 0.50)
        premium = round(base * factor, 2)
        total += premium
        breakdown.append({"relationship": m.relationship, "first_name": m.first_name,
                           "last_name": m.last_name, "premium": premium})
    return round(total, 2), breakdown


# ── Schemas ───────────────────────────────────────────────────────────────────

class MemberInput(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    relationship: str
    gender: str


class QuoteRequest(BaseModel):
    plan_id: str
    members: list[MemberInput]


class ApplyRequest(BaseModel):
    plan_id: str
    members: list[MemberInput]
    email: str
    phone: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/products", response_model=dict)
def list_products(
    tenant: Tenant = Depends(_get_tenant),
    db: Session = Depends(get_db),
):
    """Public: list active products + their active plans with coverage details."""
    products = db.query(Product).filter(
        Product.tenant_id == tenant.id,
        Product.status == "active",
    ).all()
    result = []
    for p in products:
        plans = []
        for plan in p.plans:
            if not plan.is_active:
                continue
            coverages = [{
                "id": c.id,
                "name": c.name,
                "coverage_type": c.coverage_type,
                "limit_amount": str(c.limit_amount) if c.limit_amount else None,
                "copay": str(c.copay) if c.copay else None,
            } for c in plan.coverages]
            plans.append({
                "id": plan.id,
                "name": plan.name,
                "code": plan.code,
                "plan_type": plan.plan_type,
                "base_premium": str(plan.base_premium),
                "description": plan.description,
                "coverages": coverages,
            })
        if plans:
            result.append({
                "id": p.id,
                "name": p.name,
                "code": p.code,
                "description": p.description,
                "plans": plans,
            })
    return api_response(data=result)


@router.post("/quote", response_model=dict)
def get_quote(
    payload: QuoteRequest,
    tenant: Tenant = Depends(_get_tenant),
    db: Session = Depends(get_db),
):
    """Public: calculate premium for a plan + member list."""
    plan = db.query(Plan).filter(
        Plan.id == payload.plan_id,
        Plan.tenant_id == tenant.id,
        Plan.is_active.is_(True),
    ).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")
    if not payload.members:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one member required.")

    total, breakdown = _calc_premium(float(plan.base_premium), payload.members)

    return api_response(data={
        "plan_id": plan.id,
        "plan_name": plan.name,
        "product_name": plan.product.name if plan.product else None,
        "total_premium": total,
        "breakdown": breakdown,
        "coverages": [{
            "name": c.name,
            "coverage_type": c.coverage_type,
            "limit_amount": str(c.limit_amount) if c.limit_amount else None,
        } for c in plan.coverages],
    })


@router.post("/apply", response_model=dict, status_code=status.HTTP_201_CREATED)
def submit_application(
    payload: ApplyRequest,
    tenant: Tenant = Depends(_get_tenant),
    db: Session = Depends(get_db),
):
    """Public: submit a new purchase application."""
    plan = db.query(Plan).filter(
        Plan.id == payload.plan_id,
        Plan.tenant_id == tenant.id,
        Plan.is_active.is_(True),
    ).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")
    if not payload.members:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one member required.")

    primary = next((m for m in payload.members if m.relationship == "self"), None)
    if not primary:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="One member with relationship 'self' is required.")

    valid_rel = {r.value for r in MemberRelationship}
    valid_gender = {"M", "F", "O", "U"}
    for m in payload.members:
        if m.relationship not in valid_rel:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Invalid relationship: {m.relationship}")
        if m.gender not in valid_gender:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Invalid gender: {m.gender}")

    total, _ = _calc_premium(float(plan.base_premium), payload.members)

    app = Application(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        application_number=generate_reference_number("APP"),
        product_id=plan.product_id,
        plan_id=plan.id,
        created_by=None,
        customer_email=payload.email.lower().strip(),
        customer_name=f"{primary.first_name} {primary.last_name}",
        member_count=len(payload.members),
        total_premium=Decimal(str(total)),
        status=ApplicationStatus.SUBMITTED,
        additional_info={"source": "self_service", "phone": payload.phone},
    )
    db.add(app)
    db.flush()

    for m in payload.members:
        db.add(Member(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            application_id=app.id,
            first_name=m.first_name,
            last_name=m.last_name,
            date_of_birth=m.date_of_birth,
            relationship=MemberRelationship(m.relationship),
            gender=Gender(m.gender),
            status=MemberStatus.ACTIVE,
            email=payload.email.lower().strip() if m.relationship == "self" else None,
            phone=payload.phone if m.relationship == "self" else None,
        ))

    coverages = plan.coverages
    if coverages:
        item_premium = Decimal(str(round(total / len(coverages), 2)))
        for cov in coverages:
            db.add(ApplicationItem(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                application_id=app.id,
                coverage_id=cov.id,
                premium=item_premium,
                status="pending",
            ))

    db.commit()

    return api_response(
        data={
            "application_id": app.id,
            "application_number": app.application_number,
            "total_premium": total,
            "status": app.status,
            "plan_name": plan.name,
            "product_name": plan.product.name if plan.product else None,
            "member_count": app.member_count,
        },
        message="Application submitted! Our team will review it and contact you within 1–2 business days.",
    )


@router.get("/apply/{application_id}", response_model=dict)
def get_application_status(
    application_id: str,
    tenant: Tenant = Depends(_get_tenant),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.tenant_id == tenant.id,
    ).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    return api_response(data={
        "application_id": app.id,
        "application_number": app.application_number,
        "status": app.status,
        "total_premium": float(app.total_premium),
        "member_count": app.member_count,
        "customer_name": app.customer_name,
        "customer_email": app.customer_email,
    })
