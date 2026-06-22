"""
Demo seed script — populates dev.db with realistic demo data for client presentations.

Run from the backend/ directory:
    python scripts/seed_demo.py

Safe to re-run: checks for existing demo data before inserting.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from decimal import Decimal
from datetime import datetime, date, timezone, timedelta
from passlib.context import CryptContext

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.tenant import Tenant, BrandConfig
from app.models.user import User
from app.models.product import Product, Plan, Coverage
from app.models.application import Application, ApplicationItem
from app.models.member import Member
from app.models.policy import Policy
from app.models.payment import Payment
from app.models.claim import Claim
from app.models.document import DocumentUpload
from app.constants.enums import (
    UserType, UserStatus, ProductStatus, PlanType, CoverageType,
    ApplicationStatus, PolicyStatus, MemberRelationship, MemberStatus, Gender,
    PaymentStatus, PaymentMethod, ClaimStatus, ClaimType, DocumentType,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hp(password: str) -> str:
    return pwd_context.hash(password)


def uid() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def dt(y, m, d) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


import os; engine = create_engine(os.environ.get("DATABASE_URL", "sqlite:///./dev.db"))
Session = sessionmaker(bind=engine)
db = Session()

# ── Guard: skip if already seeded ────────────────────────────────────────────
if db.query(Product).count() > 0:
    print("Demo data already present — skipping. Delete dev.db and re-run to reset.")
    db.close()
    sys.exit(0)

print("Seeding demo data …")

# ── Existing tenant & users ───────────────────────────────────────────────────
TESTCO = db.query(Tenant).filter(Tenant.code == "TESTCO").first()
if not TESTCO:
    TESTCO = Tenant(id=uid(), code="TESTCO", name="SafeLife Insurance Co.",
                    status="active", currency="USD", timezone="UTC", config={})
    db.add(TESTCO)
    db.flush()
    db.add(BrandConfig(id=uid(), tenant_id=TESTCO.id, company_name="SafeLife Insurance Co."))
    db.flush()
else:
    # Update display name
    TESTCO.name = "SafeLife Insurance Co."
    db.flush()

TID = TESTCO.id

# Create all staff users if they don't exist
for email, pw, utype, fn, ln in [
    ("admin@testco.com",        "admin123",        UserType.TENANT_ADMIN,   "Alice",  "Admin"),
    ("agent@testco.com",        "agent123",        UserType.AGENT,          "Bob",    "Agent"),
    ("underwriter@testco.com",  "underwriter123",  UserType.UNDERWRITER,    "Rachel", "Green"),
    ("claims@testco.com",       "claims123",       UserType.CLAIMS_MANAGER, "David",  "Park"),
]:
    if not db.query(User).filter(User.email == email, User.tenant_id == TID).first():
        db.add(User(id=uid(), tenant_id=TID, email=email, password_hash=hp(pw),
                    first_name=fn, last_name=ln, user_type=utype, status=UserStatus.ACTIVE))
db.flush()

ADMIN_ID = db.query(User).filter(User.email == "admin@testco.com").first().id
db.flush()

# ── Products, Plans, Coverages ────────────────────────────────────────────────

# Product 1: Health Shield Plus
P1 = Product(id=uid(), tenant_id=TID, name="Health Shield Plus", code="HSHLD",
             status=ProductStatus.ACTIVE,
             description="Comprehensive health coverage for individuals and families.")
db.add(P1); db.flush()

# Plan 1a: Gold Family
GOLD = Plan(id=uid(), tenant_id=TID, product_id=P1.id, name="Gold Family Plan", code="GOLD",
            plan_type=PlanType.FAMILY, base_premium=Decimal("1800.00"), is_active=True,
            description="Full-spectrum family coverage including maternity and dental.")
db.add(GOLD); db.flush()

for name, ctype, limit, copay in [
    ("Inpatient Hospitalization", CoverageType.HOSPITALIZATION, "150000.00", "50.00"),
    ("Outpatient Consultations",  CoverageType.OUTPATIENT,      "10000.00",  "20.00"),
    ("Dental & Oral Care",        CoverageType.DENTAL,          "5000.00",   "15.00"),
    ("Vision & Eyecare",          CoverageType.VISION,          "2000.00",   "10.00"),
    ("Maternity Benefits",        CoverageType.MATERNITY,       "20000.00",  None),
    ("Prescription Drugs",        CoverageType.PRESCRIPTION,    "8000.00",   "10.00"),
]:
    db.add(Coverage(id=uid(), tenant_id=TID, plan_id=GOLD.id, name=name,
                    coverage_type=ctype,
                    limit_amount=Decimal(limit),
                    copay=Decimal(copay) if copay else None))

# Plan 1b: Silver Individual
SILVER = Plan(id=uid(), tenant_id=TID, product_id=P1.id, name="Silver Individual Plan", code="SILVER",
              plan_type=PlanType.INDIVIDUAL, base_premium=Decimal("900.00"), is_active=True,
              description="Solid individual coverage for working professionals.")
db.add(SILVER); db.flush()

for name, ctype, limit, copay in [
    ("Inpatient Hospitalization", CoverageType.HOSPITALIZATION, "80000.00", "50.00"),
    ("Outpatient Consultations",  CoverageType.OUTPATIENT,      "6000.00",  "20.00"),
    ("Prescription Drugs",        CoverageType.PRESCRIPTION,    "4000.00",  "10.00"),
    ("Preventive Care",           CoverageType.PREVENTIVE,      "2000.00",  None),
]:
    db.add(Coverage(id=uid(), tenant_id=TID, plan_id=SILVER.id, name=name,
                    coverage_type=ctype,
                    limit_amount=Decimal(limit),
                    copay=Decimal(copay) if copay else None))

# Product 2: Basic Care
P2 = Product(id=uid(), tenant_id=TID, name="Basic Care", code="BCARE",
             status=ProductStatus.ACTIVE,
             description="Essential coverage at an affordable premium.")
db.add(P2); db.flush()

ESSENTIAL = Plan(id=uid(), tenant_id=TID, product_id=P2.id, name="Essential Plan", code="ESSENTIAL",
                 plan_type=PlanType.INDIVIDUAL, base_premium=Decimal("480.00"), is_active=True,
                 description="Core hospitalization and outpatient for budget-conscious individuals.")
db.add(ESSENTIAL); db.flush()

for name, ctype, limit, copay in [
    ("Inpatient Hospitalization", CoverageType.HOSPITALIZATION, "50000.00", "75.00"),
    ("Emergency Care",            CoverageType.EMERGENCY,       "25000.00", None),
    ("Outpatient Consultations",  CoverageType.OUTPATIENT,      "3000.00",  "25.00"),
]:
    db.add(Coverage(id=uid(), tenant_id=TID, plan_id=ESSENTIAL.id, name=name,
                    coverage_type=ctype,
                    limit_amount=Decimal(limit),
                    copay=Decimal(copay) if copay else None))

db.flush()

# ── Helper: create application + members + items ──────────────────────────────

def make_application(plan, app_status, customer_name, customer_email, members_data, source=None):
    """members_data: list of (first, last, dob_str, rel, gender)"""
    base = float(plan.base_premium)
    FACTORS = {"self": 1.0, "spouse": 0.75, "parent": 0.70, "sibling": 0.65, "child": 0.35, "dependent": 0.40}
    total = sum(round(base * FACTORS.get(rel, 0.5), 2) for *_, rel, _ in members_data)

    app = Application(
        id=uid(), tenant_id=TID,
        application_number=f"APP-DEMO-{str(uuid.uuid4())[:6].upper()}",
        product_id=plan.product_id, plan_id=plan.id,
        created_by=ADMIN_ID,
        customer_email=customer_email, customer_name=customer_name,
        member_count=len(members_data),
        total_premium=Decimal(str(round(total, 2))),
        status=app_status,
        additional_info={"source": source or "staff"},
    )
    db.add(app); db.flush()

    members = []
    for fn, ln, dob_str, rel, gender in members_data:
        m = Member(
            id=uid(), tenant_id=TID, application_id=app.id,
            first_name=fn, last_name=ln,
            date_of_birth=date.fromisoformat(dob_str),
            relationship=MemberRelationship(rel),
            gender=Gender(gender),
            status=MemberStatus.ACTIVE,
            email=customer_email if rel == "self" else None,
        )
        db.add(m); members.append(m)

    coverages = db.query(Coverage).filter(Coverage.plan_id == plan.id).all()
    if coverages:
        item_premium = Decimal(str(round(total / len(coverages), 2)))
        for cov in coverages:
            db.add(ApplicationItem(
                id=uid(), tenant_id=TID, application_id=app.id,
                coverage_id=cov.id, premium=item_premium, status="approved" if app_status == ApplicationStatus.ISSUED else "pending",
            ))
    db.flush()
    return app, members


def make_policy(app, plan, eff, exp, issued_by=None):
    policy = Policy(
        id=uid(), tenant_id=TID,
        policy_number=f"POL-DEMO-{str(uuid.uuid4())[:6].upper()}",
        application_id=app.id,
        product_id=plan.product_id, plan_id=plan.id,
        customer_name=app.customer_name,
        customer_email=app.customer_email,
        member_count=app.member_count,
        total_premium=app.total_premium,
        status=PolicyStatus.ACTIVE,
        effective_date=eff, expiry_date=exp,
        issued_by=issued_by or ADMIN_ID,
        issued_at=now_utc(),
    )
    db.add(policy); db.flush()
    return policy


def make_payment(policy, amount, method, paid_on, reference=None):
    p = Payment(
        id=uid(), tenant_id=TID,
        payment_number=f"PAY-DEMO-{str(uuid.uuid4())[:6].upper()}",
        policy_id=policy.id,
        amount=Decimal(str(amount)),
        method=method, status=PaymentStatus.SUCCESS,
        reference=reference,
        paid_at=paid_on,
    )
    db.add(p); return p


def make_claim(policy, member_id, ctype, cstatus, incident, desc, claimed, approved=None):
    c = Claim(
        id=uid(), tenant_id=TID,
        claim_number=f"CLM-DEMO-{str(uuid.uuid4())[:6].upper()}",
        policy_id=policy.id,
        member_id=member_id,
        claim_type=ctype, status=cstatus,
        incident_date=incident,
        description=desc,
        claimed_amount=Decimal(str(claimed)),
        approved_amount=Decimal(str(approved)) if approved else None,
    )
    db.add(c); return c


def make_customer_account(policy, email, pw, fn, ln, dob):
    if db.query(User).filter(User.email == email, User.tenant_id == TID).first():
        return
    db.add(User(
        id=uid(), tenant_id=TID,
        email=email, password_hash=hp(pw),
        first_name=fn, last_name=ln,
        user_type=UserType.CUSTOMER,
        status=UserStatus.ACTIVE,
        extra_data={"policy_id": policy.id},
    ))
    db.flush()


# ── Policy 1: Wilson Family (Gold) ────────────────────────────────────────────
app1, members1 = make_application(
    GOLD, ApplicationStatus.ISSUED,
    "James Wilson", "james.wilson@email.com",
    [
        ("James",  "Wilson", "1982-06-15", "self",   "male"),
        ("Sarah",  "Wilson", "1984-09-22", "spouse", "female"),
        ("Emma",   "Wilson", "2016-03-10", "child",  "female"),
    ],
)
pol1 = make_policy(app1, GOLD, dt(2026, 1, 1), dt(2027, 1, 1))
# Annual premium split into quarterly payments
make_payment(pol1, 945.00, PaymentMethod.BANK_TRANSFER, dt(2026, 1, 5),  "WT-2026-JAN-001")
make_payment(pol1, 945.00, PaymentMethod.BANK_TRANSFER, dt(2026, 4, 5),  "WT-2026-APR-001")
# Claims
james_id = members1[0].id
emma_id  = members1[2].id
make_claim(pol1, james_id, ClaimType.HOSPITALIZATION, ClaimStatus.APPROVED,
           date(2026, 2, 14), "Appendectomy — 3-day hospital stay",
           3800.00, approved=3420.00)
make_claim(pol1, emma_id,  ClaimType.OUTPATIENT,      ClaimStatus.SUBMITTED,
           date(2026, 4, 28), "Paediatric consultation and blood panel",
           350.00)
make_claim(pol1, james_id, ClaimType.PHARMACY,        ClaimStatus.PAID,
           date(2026, 3, 10), "Post-surgery prescription medications",
           280.00, approved=280.00)
# Documents
db.add(DocumentUpload(
    id=uid(), tenant_id=TID,
    file_name="policy-document-wilson.pdf", file_path="demo/docs/policy-wilson.pdf",
    file_size=245000, mime_type="application/pdf",
    document_type=DocumentType.POLICY_DOCUMENT,
    entity_type="policy", entity_id=pol1.id,
    uploaded_by=ADMIN_ID, validation_status="valid",
))
db.add(DocumentUpload(
    id=uid(), tenant_id=TID,
    file_name="invoice-Q1-2026.pdf", file_path="demo/docs/invoice-wilson-q1.pdf",
    file_size=92000, mime_type="application/pdf",
    document_type=DocumentType.INVOICE,
    entity_type="policy", entity_id=pol1.id,
    uploaded_by=ADMIN_ID, validation_status="valid",
))
db.flush()
make_customer_account(pol1, "james.wilson@email.com", "Customer123", "James", "Wilson", "1982-06-15")

# ── Policy 2: Michael Chen (Silver) ──────────────────────────────────────────
app2, members2 = make_application(
    SILVER, ApplicationStatus.ISSUED,
    "Michael Chen", "michael.chen@email.com",
    [("Michael", "Chen", "1990-11-30", "self", "male")],
)
pol2 = make_policy(app2, SILVER, dt(2026, 2, 1), dt(2027, 2, 1))
make_payment(pol2, 900.00, PaymentMethod.CARD, dt(2026, 2, 1), "CARD-2026-0201")
make_claim(pol2, members2[0].id, ClaimType.DENTAL, ClaimStatus.UNDER_REVIEW,
           date(2026, 4, 10), "Root canal treatment — lower left molar", 1200.00)
db.add(DocumentUpload(
    id=uid(), tenant_id=TID,
    file_name="policy-document-chen.pdf", file_path="demo/docs/policy-chen.pdf",
    file_size=238000, mime_type="application/pdf",
    document_type=DocumentType.POLICY_DOCUMENT,
    entity_type="policy", entity_id=pol2.id,
    uploaded_by=ADMIN_ID, validation_status="valid",
))
db.flush()
make_customer_account(pol2, "michael.chen@email.com", "Customer123", "Michael", "Chen", "1990-11-30")

# ── Policy 3: Emily Rodriguez (Essential) ────────────────────────────────────
app3, members3 = make_application(
    ESSENTIAL, ApplicationStatus.ISSUED,
    "Emily Rodriguez", "emily.rodriguez@email.com",
    [("Emily", "Rodriguez", "1995-07-04", "self", "female")],
)
pol3 = make_policy(app3, ESSENTIAL, dt(2026, 3, 1), dt(2027, 3, 1))
make_payment(pol3, 480.00, PaymentMethod.UPI, dt(2026, 3, 1), "UPI-2026-0301")
db.add(DocumentUpload(
    id=uid(), tenant_id=TID,
    file_name="policy-document-rodriguez.pdf", file_path="demo/docs/policy-rodriguez.pdf",
    file_size=219000, mime_type="application/pdf",
    document_type=DocumentType.POLICY_DOCUMENT,
    entity_type="policy", entity_id=pol3.id,
    uploaded_by=ADMIN_ID, validation_status="valid",
))
db.add(DocumentUpload(
    id=uid(), tenant_id=TID,
    file_name="application-form-rodriguez.pdf", file_path="demo/docs/app-rodriguez.pdf",
    file_size=180000, mime_type="application/pdf",
    document_type=DocumentType.APPLICATION_FORM,
    entity_type="policy", entity_id=pol3.id,
    uploaded_by=ADMIN_ID, validation_status="valid",
))
db.flush()
# No customer account — shows registration flow in demo

# ── Pending Applications (staff review queue) ─────────────────────────────────
make_application(
    GOLD, ApplicationStatus.UNDER_REVIEW,
    "Robert Kim", "robert.kim@email.com",
    [
        ("Robert", "Kim",  "1978-04-20", "self",   "male"),
        ("Grace",  "Kim",  "1980-08-15", "spouse", "female"),
        ("Liam",   "Kim",  "2012-01-25", "child",  "male"),
        ("Ava",    "Kim",  "2015-06-30", "child",  "female"),
    ],
)
make_application(
    SILVER, ApplicationStatus.SUBMITTED,
    "Linda Park", "linda.park@email.com",
    [("Linda", "Park", "1988-12-01", "self", "female")],
    source="self_service",
)
make_application(
    ESSENTIAL, ApplicationStatus.SUBMITTED,
    "David Brown", "david.brown@email.com",
    [("David", "Brown", "2000-05-17", "self", "male")],
    source="self_service",
)
make_application(
    GOLD, ApplicationStatus.APPROVED,
    "Priya Sharma", "priya.sharma@email.com",
    [
        ("Priya",  "Sharma", "1985-03-28", "self",   "female"),
        ("Arjun",  "Sharma", "1983-10-14", "spouse", "male"),
    ],
)

db.flush()

db.commit()
db.close()

print("✓  Demo data seeded successfully!\n")
print("=" * 58)
print("  DEMO CREDENTIALS & PORTAL URLS")
print("=" * 58)
print()
print("STAFF PORTAL  →  http://localhost:5173")
print(f"  admin@testco.com        / admin123")
print(f"  agent@testco.com        / password123")
print(f"  underwriter@testco.com  / underwriter123")
print(f"  claims@testco.com       / claims123")
print()
print("PURCHASE PORTAL  →  http://localhost:5173/buy")
print(f"  Company code: TESTCO")
print()
print("MEMBER PORTAL  →  http://localhost:5173/portal")
print(f"  james.wilson@email.com  / Customer123  (Gold, family, 3 members)")
print(f"  michael.chen@email.com  / Customer123  (Silver, 1 claim under review)")
print()
print("REGISTER DEMO  →  http://localhost:5173/portal/register")
print(f"  Company code: TESTCO")
print(f"  Emily Rodriguez's policy: use her policy number + DOB 1995-07-04")
print(f"  (find her policy number in the staff portal → Policies)")
print()
print("=" * 58)
