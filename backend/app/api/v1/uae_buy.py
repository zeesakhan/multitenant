"""
UAE Buy Router — Adamjee Insurance self-service purchase journey.
Public endpoints: no authentication required.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db
from app.models.product import Product, Plan, Coverage
from app.models.application import Application, ApplicationItem
from app.models.member import Member
from app.models.payment import Payment
from app.models.tenant import Tenant
from app.constants.enums import (
    ApplicationStatus, MemberRelationship, MemberStatus, Gender,
    PaymentStatus, PaymentMethod,
)
from app.utils.formatters import api_response, generate_reference_number
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date
import uuid
from decimal import Decimal

router = APIRouter(prefix="/uae-buy", tags=["UAE Adamjee Purchase"])

ADAMJEE_CODE = "ADAMJEE"

# ── Relationship premium factors (UAE market standard) ─────────────────────
_FACTORS = {
    "self": 1.00,
    "spouse": 0.80,
    "child": 0.40,
    "parent": 0.75,
    "sibling": 0.65,
    "dependent": 0.45,
}

UAE_REGULATIONS = [
    {
        "ref": "Dubai Law No. 11 of 2013",
        "title": "Dubai Health Insurance Law",
        "summary": (
            "Mandates health insurance for all residents in Dubai. "
            "Employers must provide insurance for employees and their dependants. "
            "Individuals must obtain insurance if their employer does not provide it."
        ),
    },
    {
        "ref": "Cabinet Resolution No. 49 of 2019",
        "title": "Essential Benefits Plan (EBP)",
        "summary": (
            "Defines the minimum package of health benefits that every insured "
            "person in Dubai must receive. Includes inpatient, outpatient, emergency, "
            "maternity, and pharmacy benefits."
        ),
    },
    {
        "ref": "Federal Law No. 6 of 2007",
        "title": "Insurance Authority Regulations",
        "summary": (
            "Governs all insurance operations in the UAE. Insurers must be licensed "
            "by the Insurance Authority (now integrated into the Central Bank of UAE). "
            "Policy wording must be transparent and in Arabic or bilingual."
        ),
    },
    {
        "ref": "DHA Minimum Benefits Package",
        "title": "Dubai Health Authority Minimum Benefits",
        "summary": (
            "All DHA-compliant plans must cover: inpatient hospitalization, "
            "outpatient services, emergency care, maternity, pharmacy, and diagnostics. "
            "No annual deductible may exceed AED 1,000 per person."
        ),
    },
    {
        "ref": "Federal Decree-Law No. 45 of 2021",
        "title": "UAE Personal Data Protection Law (PDPL)",
        "summary": (
            "Regulates the collection, processing, and storage of personal data "
            "in the UAE. You have the right to access, correct, and request deletion "
            "of your personal data. Data collected is used solely for insurance "
            "underwriting, policy administration, and regulatory compliance."
        ),
    },
    {
        "ref": "ISA Circular No. 33 of 2019",
        "title": "Anti-Fraud and Misrepresentation",
        "summary": (
            "Any misrepresentation of medical history, identity, or personal details "
            "is a criminal offence under UAE law and will result in policy cancellation "
            "and potential prosecution."
        ),
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_adamjee(db: Session) -> Tenant:
    t = db.query(Tenant).filter(Tenant.code == ADAMJEE_CODE).first()
    if not t:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Adamjee Insurance service is temporarily unavailable.",
        )
    return t


def _calc_premium(base: float, members: list) -> tuple[float, list]:
    breakdown = []
    total = 0.0
    for m in members:
        factor = _FACTORS.get(m.relationship, 0.50)
        premium = round(base * factor, 2)
        total += premium
        breakdown.append({
            "relationship": m.relationship,
            "first_name": m.first_name,
            "last_name": m.last_name,
            "premium": premium,
            "factor": factor,
        })
    return round(total, 2), breakdown


# ── Schemas ─────────────────────────────────────────────────────────────────

class UAEMemberInput(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    relationship: str
    gender: str
    nationality: Optional[str] = None
    passport_number: Optional[str] = None
    emirates_id: Optional[str] = None
    document_expiry: Optional[date] = None
    visa_type: Optional[str] = None
    place_of_birth: Optional[str] = None


class UAEQuoteRequest(BaseModel):
    plan_id: str
    members: list[UAEMemberInput]


class UAEApplyRequest(BaseModel):
    plan_id: str
    members: list[UAEMemberInput]
    email: str
    phone: str
    pre_existing_conditions: bool = False
    pre_existing_details: Optional[str] = None
    agreed_to_terms: bool
    agreed_to_regulations: bool

    @field_validator("agreed_to_terms", "agreed_to_regulations")
    @classmethod
    def must_agree(cls, v: bool, info) -> bool:
        if not v:
            raise ValueError(f"{info.field_name} must be accepted to proceed.")
        return v


class PaymentRequest(BaseModel):
    method: str  # "card" | "apple_pay" | "google_pay" | "bank_transfer"
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None
    cardholder_name: Optional[str] = None


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/info")
def get_adamjee_info(db: Session = Depends(get_db)):
    """Public: Adamjee tenant branding & contact info."""
    tenant = _get_adamjee(db)
    brand = tenant.brand_config
    return api_response(data={
        "tenant_id": tenant.id,
        "tenant_code": tenant.code,
        "name": tenant.name,
        "currency": tenant.currency,
        "config": tenant.config,
        "brand": {
            "company_name": brand.company_name if brand else tenant.name,
            "primary_color": brand.primary_color if brand else "#0055A5",
            "secondary_color": brand.secondary_color if brand else "#F59E0B",
            "support_email": brand.support_email if brand else None,
            "support_phone": brand.support_phone if brand else None,
        } if brand else {},
    })


@router.get("/plans")
def list_adamjee_plans(db: Session = Depends(get_db)):
    """Public: all active Adamjee plans with full coverage details."""
    tenant = _get_adamjee(db)
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
            coverages = []
            for c in plan.coverages:
                coverages.append({
                    "id": c.id,
                    "name": c.name,
                    "coverage_type": c.coverage_type,
                    "limit_amount": float(c.limit_amount) if c.limit_amount else None,
                    "copay": float(c.copay) if c.copay else None,
                    "description": (c.config or {}).get("description", ""),
                })
            plans.append({
                "id": plan.id,
                "name": plan.name,
                "code": plan.code,
                "plan_type": plan.plan_type,
                "base_premium": float(plan.base_premium),
                "description": plan.description,
                "coverages": coverages,
                "highlights": _plan_highlights(plan.name),
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


def _plan_highlights(name: str) -> list[str]:
    name_upper = name.upper()
    base = [
        "AED 1,000,000 annual aggregate limit",
        "DHA Compliant · TPA: MEDNET",
        "Maternity up to AED 10,000",
        "Dental up to AED 3,500/year",
        "Pre-existing conditions covered (AED 150k sub-limit)",
    ]
    if "GOLD" in name_upper:
        return ["American Hospital, Mediclinic City & top-tier hospitals"] + base
    if "SILVER PREMIUM" in name_upper or "SIL-PRE" in name_upper:
        return ["Premium private hospital network across UAE"] + base
    if "SILVER CLASSIC" in name_upper or "SIL-CLA" in name_upper:
        return ["Silver Classic private hospital & clinic network"] + base
    if "EMERALD" in name_upper:
        return ["Emerald mid-tier private hospital network"] + base
    if "PEARL" in name_upper:
        return ["Pearl network — solid private clinic coverage"] + base
    if "GREEN" in name_upper:
        return ["Government hospitals + selected private clinics"] + base
    if "SILK" in name_upper:
        return ["Essential coverage — government hospital network"] + base
    return base


@router.post("/ocr")
async def ocr_document(file: UploadFile = File(...)):
    """
    Upload a passport or Emirates ID image for OCR extraction.
    Returns extracted fields. Falls back gracefully if OCR library missing.
    """
    allowed_types = {"image/jpeg", "image/png", "image/jpg", "image/webp", "application/pdf"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported file type. Upload JPEG, PNG, or PDF.",
        )

    contents = await file.read()
    extracted = _run_ocr(contents, file.content_type, file.filename or "")

    return api_response(
        data=extracted,
        message="Document scanned successfully." if extracted.get("ocr_success") else
                "Could not auto-read document. Please fill in details manually.",
    )


def _run_ocr(data: bytes, content_type: str, filename: str) -> dict:
    result = {
        "ocr_success": False,
        "document_type": "passport",
        "first_name": "",
        "last_name": "",
        "date_of_birth": "",
        "nationality": "",
        "passport_number": "",
        "emirates_id": "",
        "document_expiry": "",
        "gender": "",
    }

    try:
        import pytesseract
        from PIL import Image
        import io
        import re

        if "pdf" in content_type:
            return result  # PDF OCR needs extra deps, skip in dev

        img = Image.open(io.BytesIO(data))
        text = pytesseract.image_to_string(img)

        # Try Emirates ID pattern: 784-XXXX-XXXXXXX-X
        eid_match = re.search(r'784[-\s]?\d{4}[-\s]?\d{7}[-\s]?\d', text)
        if eid_match:
            result["emirates_id"] = re.sub(r'[\s]', '-', eid_match.group())
            result["document_type"] = "emirates_id"

        # Try passport MRZ lines (TD3: two 44-char lines)
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) >= 40]
        mrz_lines = [l for l in lines if re.match(r'^[A-Z0-9<]{40,}$', l)]
        if len(mrz_lines) >= 2:
            parsed = _parse_mrz(mrz_lines[0], mrz_lines[1])
            if parsed:
                result.update(parsed)
                result["document_type"] = "passport"

        # Generic name extraction fallback
        name_match = re.search(r'(?:Name|NAME)[:\s]+([A-Z][a-z]+)\s+([A-Z][a-z]+)', text)
        if name_match and not result["first_name"]:
            result["first_name"] = name_match.group(1)
            result["last_name"] = name_match.group(2)

        result["ocr_success"] = bool(
            result["first_name"] or result["passport_number"] or result["emirates_id"]
        )

    except ImportError:
        pass  # pytesseract/Pillow not installed — return empty fields
    except Exception:
        pass

    return result


def _parse_mrz(line1: str, line2: str) -> Optional[dict]:
    import re
    try:
        if len(line1) < 44 or len(line2) < 44:
            return None
        raw_names = line1[5:44].split("<<", 1)
        surname = raw_names[0].replace("<", " ").strip()
        given = raw_names[1].replace("<", " ").strip() if len(raw_names) > 1 else ""

        passport_num = line2[0:9].replace("<", "").strip()
        nationality = line2[10:13].replace("<", "").strip()
        dob_raw = line2[13:19]
        sex = line2[20]
        expiry_raw = line2[21:27]

        def _mrz_date(s: str) -> str:
            if len(s) != 6:
                return ""
            yy, mm, dd = s[:2], s[2:4], s[4:6]
            year = f"19{yy}" if int(yy) > 30 else f"20{yy}"
            return f"{year}-{mm}-{dd}"

        return {
            "last_name": surname,
            "first_name": given,
            "passport_number": passport_num,
            "nationality": nationality,
            "date_of_birth": _mrz_date(dob_raw),
            "document_expiry": _mrz_date(expiry_raw),
            "gender": "M" if sex == "M" else "F",
        }
    except Exception:
        return None


@router.post("/quote")
def get_uae_quote(payload: UAEQuoteRequest, db: Session = Depends(get_db)):
    """Public: calculate premium for selected plan and members."""
    tenant = _get_adamjee(db)
    plan = db.query(Plan).filter(
        Plan.id == payload.plan_id,
        Plan.tenant_id == tenant.id,
        Plan.is_active.is_(True),
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")
    if not payload.members:
        raise HTTPException(status_code=400, detail="At least one member required.")

    total, breakdown = _calc_premium(float(plan.base_premium), payload.members)

    return api_response(data={
        "tenant_id": tenant.id,
        "plan_id": plan.id,
        "plan_name": plan.name,
        "base_premium": float(plan.base_premium),
        "currency": tenant.currency,
        "total_premium": total,
        "total_monthly": round(total / 12, 2),
        "breakdown": breakdown,
        "coverages": [{
            "name": c.name,
            "coverage_type": c.coverage_type,
            "limit_amount": float(c.limit_amount) if c.limit_amount else None,
            "copay": float(c.copay) if c.copay else None,
            "description": (c.config or {}).get("description", ""),
        } for c in plan.coverages],
    })


@router.get("/regulations")
def get_regulations():
    """Public: UAE insurance regulations and compliance summary."""
    return api_response(data={
        "regulations": UAE_REGULATIONS,
        "disclaimer": (
            "This summary is for informational purposes only. "
            "Full policy terms and conditions are provided in the policy schedule. "
            "Adamjee Insurance is licensed by the Insurance Authority of the UAE."
        ),
    })


@router.post("/apply", status_code=201)
def submit_uae_application(payload: UAEApplyRequest, db: Session = Depends(get_db)):
    """Public: submit a UAE-compliant insurance application."""
    tenant = _get_adamjee(db)
    plan = db.query(Plan).filter(
        Plan.id == payload.plan_id,
        Plan.tenant_id == tenant.id,
        Plan.is_active.is_(True),
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")
    if not payload.members:
        raise HTTPException(status_code=400, detail="At least one member required.")

    primary = next((m for m in payload.members if m.relationship == "self"), None)
    if not primary:
        raise HTTPException(status_code=400, detail="Primary insured (relationship=self) required.")

    # Validate UAE identity: primary must have passport or Emirates ID
    if not primary.passport_number and not primary.emirates_id:
        raise HTTPException(
            status_code=422,
            detail="Primary insured must provide a Passport number or Emirates ID.",
        )

    valid_rel = {r.value for r in MemberRelationship}
    valid_gender = {"M", "F", "O", "U"}
    for m in payload.members:
        if m.relationship not in valid_rel:
            raise HTTPException(status_code=422, detail=f"Invalid relationship: {m.relationship}")
        if m.gender not in valid_gender:
            raise HTTPException(status_code=422, detail=f"Invalid gender: {m.gender}")

    total, breakdown = _calc_premium(float(plan.base_premium), payload.members)

    app = Application(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        application_number=generate_reference_number("UAE"),
        product_id=plan.product_id,
        plan_id=plan.id,
        created_by=None,
        customer_email=payload.email.lower().strip(),
        customer_name=f"{primary.first_name} {primary.last_name}",
        member_count=len(payload.members),
        total_premium=Decimal(str(total)),
        status=ApplicationStatus.PENDING_PAYMENT,
        additional_info={
            "source": "uae_self_service",
            "phone": payload.phone,
            "pre_existing_conditions": payload.pre_existing_conditions,
            "pre_existing_details": payload.pre_existing_details,
            "agreed_to_terms": payload.agreed_to_terms,
            "agreed_to_regulations": payload.agreed_to_regulations,
            "currency": tenant.currency,
            "premium_breakdown": breakdown,
        },
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
            national_id=m.emirates_id or m.passport_number,
            passport_number=m.passport_number,
            emirates_id=m.emirates_id,
            nationality=m.nationality,
            visa_type=m.visa_type,
            document_expiry=m.document_expiry,
            place_of_birth=m.place_of_birth,
        ))

    coverages = plan.coverages
    if coverages:
        item_premium = Decimal(str(round(total / max(len(coverages), 1), 2)))
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
            "status": app.status,
            "currency": tenant.currency,
            "total_premium": total,
            "total_monthly": round(total / 12, 2),
            "plan_name": plan.name,
            "member_count": app.member_count,
        },
        message="Application created. Please complete payment to activate your policy.",
    )


@router.post("/payment/{application_id}", status_code=201)
def initiate_payment(
    application_id: str,
    payload: PaymentRequest,
    db: Session = Depends(get_db),
):
    """Public: initiate payment for an Adamjee application (creates policy on success)."""
    from app.models.policy import Policy
    from app.constants.enums import PolicyStatus
    from datetime import datetime, timezone, timedelta

    tenant = _get_adamjee(db)
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.tenant_id == tenant.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    if app.status not in (ApplicationStatus.PENDING_PAYMENT, ApplicationStatus.SUBMITTED):
        raise HTTPException(status_code=409, detail=f"Application status '{app.status}' does not allow payment.")

    method_map = {
        "card": PaymentMethod.CARD,
        "apple_pay": PaymentMethod.WALLET,
        "google_pay": PaymentMethod.WALLET,
        "bank_transfer": PaymentMethod.BANK_TRANSFER,
    }
    pay_method = method_map.get(payload.method, PaymentMethod.CARD)

    plan = db.query(Plan).filter(Plan.id == app.plan_id).first()

    # Issue policy
    now = datetime.now(timezone.utc)
    policy = Policy(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        policy_number=generate_reference_number("POL"),
        application_id=app.id,
        product_id=app.product_id,
        plan_id=app.plan_id,
        customer_name=app.customer_name,
        customer_email=app.customer_email,
        member_count=app.member_count,
        total_premium=app.total_premium,
        status=PolicyStatus.ACTIVE,
        effective_date=now,
        expiry_date=now + timedelta(days=365),
    )
    db.add(policy)
    db.flush()

    payment = Payment(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        policy_id=policy.id,
        payment_number=generate_reference_number("PAY"),
        amount=app.total_premium,
        method=pay_method,
        status=PaymentStatus.SUCCESS,
        reference=generate_reference_number("TXN"),
        notes=f"method={payload.method} brand={payload.card_brand or 'N/A'} last4={payload.card_last4 or 'XXXX'} cardholder={payload.cardholder_name or 'N/A'}",
        paid_at=now,
    )
    db.add(payment)

    app.status = ApplicationStatus.ISSUED
    app.additional_info = {
        **(app.additional_info or {}),
        "payment_reference": payment.reference,
        "payment_number": payment.payment_number,
        "payment_method": payload.method,
        "policy_id": policy.id,
        "policy_number": policy.policy_number,
    }

    db.commit()

    # Send policy confirmation email (logs to console in dev when SMTP not configured)
    try:
        from app.services.email_service import EmailService
        annual = float(app.total_premium)
        EmailService().notify_adamjee_policy_issued(
            customer_email=app.customer_email,
            customer_name=app.customer_name,
            policy_number=policy.policy_number,
            plan_name=plan.name if hasattr(plan, "name") else "Adamjee Plan",
            effective_date=now.date().isoformat(),
            expiry_date=(now + timedelta(days=365)).date().isoformat(),
            annual_premium_aed=f"{annual:,.2f}",
            monthly_premium_aed=f"{annual / 12:,.2f}",
            member_count=app.member_count,
            payment_reference=payment.reference,
            application_number=app.application_number,
        )
    except Exception:
        pass  # never block the response on email failure

    return api_response(
        data={
            "payment_id": payment.id,
            "payment_number": payment.payment_number,
            "reference": payment.reference,
            "status": payment.status,
            "amount": float(payment.amount),
            "currency": tenant.currency,
            "application_id": app.id,
            "application_number": app.application_number,
            "policy_number": policy.policy_number,
            "policy_effective": now.date().isoformat(),
            "policy_expiry": (now + timedelta(days=365)).date().isoformat(),
        },
        message="Payment successful! Your policy is now active. A confirmation email will be sent shortly.",
    )


@router.get("/payment/{application_id}/status")
def get_payment_status(application_id: str, db: Session = Depends(get_db)):
    """Public: check application and payment status."""
    tenant = _get_adamjee(db)
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.tenant_id == tenant.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    return api_response(data={
        "application_id": app.id,
        "application_number": app.application_number,
        "status": app.status,
        "total_premium": float(app.total_premium),
        "currency": tenant.currency,
        "customer_name": app.customer_name,
        "customer_email": app.customer_email,
        "payment_reference": (app.additional_info or {}).get("payment_reference"),
    })
