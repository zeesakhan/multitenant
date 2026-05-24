from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException

from config import get_settings
from app.utils.logger import configure_logging
from app.middleware.tenant_context import TenantContextMiddleware
from app.middleware.audit_logger import AuditLoggerMiddleware
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.api.v1 import v1_router
from app.api.health import router as health_router

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.utils.logger import get_logger
    logger = get_logger("startup")
    logger.info("Health Insurance Platform started", version=settings.app_version)

    if "sqlite" in settings.database_url:
        _bootstrap_sqlite_dev()

    yield


_INSECURE_DEFAULTS = {
    "your-secret-key-change-in-production",
    "your-encryption-key-change-in-production",
}
if not settings.debug:
    if settings.secret_key in _INSECURE_DEFAULTS:
        raise RuntimeError("SECRET_KEY must be changed before running in production.")
    if settings.encryption_key in _INSECURE_DEFAULTS:
        raise RuntimeError("ENCRYPTION_KEY must be changed before running in production.")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Custom middleware (order matters: first added = outermost)
app.add_middleware(AuditLoggerMiddleware)
app.add_middleware(TenantContextMiddleware)

# Exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Routers
app.include_router(health_router)
app.include_router(v1_router)


def _bootstrap_sqlite_dev():
    """Create tables and seed demo data for local SQLite dev mode."""
    from app.models.base import Base
    from app.db.database import _get_engine, _get_session_factory
    import app.models  # ensure all models are registered
    import app.models.application  # noqa: F401
    import app.models.policy       # noqa: F401
    import app.models.member       # noqa: F401
    import app.models.payment      # noqa: F401
    import app.models.claim        # noqa: F401
    from app.models import product  # noqa: F401

    engine = _get_engine()
    Base.metadata.create_all(bind=engine)

    # Add UAE member columns if missing (SQLite ALTER TABLE is limited)
    from sqlalchemy import text, inspect as sa_inspect
    insp = sa_inspect(engine)
    existing_cols = {c["name"] for c in insp.get_columns("members")}
    uae_cols = {
        "passport_number": "VARCHAR(50)",
        "emirates_id": "VARCHAR(25)",
        "nationality": "VARCHAR(100)",
        "visa_type": "VARCHAR(80)",
        "document_expiry": "DATE",
        "place_of_birth": "VARCHAR(100)",
    }
    with engine.connect() as conn:
        for col, col_type in uae_cols.items():
            if col not in existing_cols:
                conn.execute(text(f"ALTER TABLE members ADD COLUMN {col} {col_type}"))
        conn.commit()

    from app.models.tenant import Tenant, BrandConfig
    from app.models.user import User
    from app.models.product import Product, Plan, Coverage
    from app.constants.enums import (
        TenantStatus, UserType, UserStatus, ProductStatus, PlanType, CoverageType
    )
    from app.services.user_service import hash_password
    from decimal import Decimal
    import uuid

    factory = _get_session_factory()
    db = factory()
    try:
        if db.query(Tenant).filter(Tenant.code == "TESTCO").first():
            # Re-seed Adamjee if not present yet
            _seed_adamjee_if_needed(db, hash_password, Tenant, BrandConfig, User, Product, Plan, Coverage,
                                    TenantStatus, UserType, UserStatus, ProductStatus, PlanType, CoverageType,
                                    Decimal, uuid)
            db.commit()
            return  # TESTCO already seeded

        tenant = Tenant(
            id=str(uuid.uuid4()),
            code="TESTCO",
            name="Test Insurance Co",
            status=TenantStatus.ACTIVE,
            currency="USD",
            timezone="UTC",
            config={},
        )
        db.add(tenant)
        db.flush()

        db.add(BrandConfig(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            company_name="Test Insurance Co",
        ))

        db.add(User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email="admin@testco.com",
            password_hash=hash_password("admin123"),
            first_name="Admin",
            last_name="User",
            user_type=UserType.TENANT_ADMIN,
            status=UserStatus.ACTIVE,
        ))

        db.add(User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            email="agent@testco.com",
            password_hash=hash_password("password123"),
            first_name="John",
            last_name="Agent",
            user_type=UserType.AGENT,
            status=UserStatus.ACTIVE,
        ))

        # Super admin tenant + user (needed for tenant management)
        sys_tenant = Tenant(
            id=str(uuid.uuid4()),
            code="SYSTEM",
            name="System",
            status=TenantStatus.ACTIVE,
            currency="USD",
            timezone="UTC",
            config={},
        )
        db.add(sys_tenant)
        db.flush()
        db.add(BrandConfig(
            id=str(uuid.uuid4()),
            tenant_id=sys_tenant.id,
            company_name="System",
        ))
        db.add(User(
            id=str(uuid.uuid4()),
            tenant_id=sys_tenant.id,
            email="superadmin@system.com",
            password_hash=hash_password("super123"),
            first_name="Super",
            last_name="Admin",
            user_type=UserType.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
        ))

        # Seed Adamjee Insurance tenant
        _seed_adamjee_if_needed(db, hash_password, Tenant, BrandConfig, User, Product, Plan, Coverage,
                                TenantStatus, UserType, UserStatus, ProductStatus, PlanType, CoverageType,
                                Decimal, uuid)

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _seed_adamjee_if_needed(db, hash_password, Tenant, BrandConfig, User, Product, Plan, Coverage,
                             TenantStatus, UserType, UserStatus, ProductStatus, PlanType, CoverageType,
                             Decimal, uuid):
    if db.query(Tenant).filter(Tenant.code == "ADAMJEE").first():
        return

    tenant = Tenant(
        id=str(uuid.uuid4()),
        code="ADAMJEE",
        name="Adamjee Insurance",
        status=TenantStatus.ACTIVE,
        currency="AED",
        timezone="Asia/Dubai",
        config={
            "country": "UAE",
            "tpa": "MEDNET",
            "dha_compliant": True,
            "support_phone": "+971-4-XXX-XXXX",
            "support_email": "customercare@adamjeeinsurance.ae",
            "website": "https://adamjeeinsurance.ae",
        },
    )
    db.add(tenant)
    db.flush()

    db.add(BrandConfig(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        company_name="Adamjee Insurance",
        primary_color="#0055A5",
        secondary_color="#F59E0B",
        support_email="customercare@adamjeeinsurance.ae",
        support_phone="+971-4-XXX-XXXX",
    ))

    db.add(User(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        email="admin@adamjee.ae",
        password_hash=hash_password("adamjee123"),
        first_name="Adamjee",
        last_name="Admin",
        user_type=UserType.TENANT_ADMIN,
        status=UserStatus.ACTIVE,
    ))

    product = Product(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        code="ADJ-FAMILY-CARE",
        name="Adamjee DHA Family Care",
        description=(
            "DHA Compliant health insurance with worldwide coverage. "
            "Annual aggregate limit AED 1,000,000 per person. TPA: MEDNET. "
            "Available in 7 network tiers to suit every budget."
        ),
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.flush()

    PLAN_TIERS = [
        ("GOLD",           "ADJ-GOLD",      4500.00, "Gold premium hospital network — American Hospital, Mediclinic City, Cleveland Clinic Abu Dhabi and top-tier providers."),
        ("SILVER PREMIUM", "ADJ-SIL-PRE",   3400.00, "Silver Premium network — excellent private hospitals and specialist centres across UAE."),
        ("SILVER CLASSIC", "ADJ-SIL-CLA",   2600.00, "Silver Classic network — strong private hospital access at a competitive premium."),
        ("EMERALD",        "ADJ-EMERALD",   2100.00, "Emerald network — comprehensive mid-tier private hospital and clinic network."),
        ("PEARL",          "ADJ-PEARL",     1800.00, "Pearl network — solid coverage with good private clinic access across Emirates."),
        ("GREEN",          "ADJ-GREEN",     1500.00, "Green network — government hospitals plus selected private clinics, great value."),
        ("SILK ROAD",      "ADJ-SILK",      1200.00, "Silk Road network — essential DHA-compliant coverage, government hospital network."),
    ]

    COVERAGES = [
        ("Inpatient Hospitalization",  "hospitalization", 1_000_000, None,  "Private room; ICU; surgeon & anaesthetist fees; organ transplant."),
        ("Outpatient Consultation",    "outpatient",       None,      20.0,  "GP & specialist visits. Co-pay: 20% (max AED 50 per visit)."),
        ("Diagnostics & Lab Tests",    "outpatient",       None,       0.0,  "All lab tests and diagnostics. 0% co-pay."),
        ("Pharmaceuticals",            "prescription",     None,       0.0,  "Prescribed medications per DHA formulary. 0% co-pay."),
        ("Dental",                     "dental",          3_500,      20.0,  "Annual sub-limit AED 3,500. 20% co-pay."),
        ("Maternity",                  "maternity",       10_000,      0.0,  "Normal & caesarean delivery, AED 10,000 each. Newborn first 30 days covered."),
        ("Physiotherapy",              "wellness",         None,        0.0,  "Up to 15 sessions per year. 0% co-pay."),
        ("Alternative Medicine",       "wellness",         1_600,       0.0,  "Homeopathy, chiropractic, acupuncture — AED 1,600/year reimbursement."),
        ("Mental Health",              "mental_health",    None,        0.0,  "Emergency mental health treatments covered."),
        ("Vaccination",                "preventive",       None,        0.0,  "All vaccinations per UAE MOH immunisation schedule."),
        ("Pre-existing Conditions",    "hospitalization", 150_000,      0.0,  "All declared chronic & pre-existing conditions. Sub-limit AED 150,000."),
        ("Ambulance",                  "emergency",        None,        0.0,  "Emergency ambulance with hospital admission."),
        ("Repatriation",               "emergency",        7_500,       0.0,  "Repatriation of mortal remains up to AED 7,500."),
    ]

    for plan_name, plan_code, base_premium, description in PLAN_TIERS:
        plan = Plan(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            product_id=product.id,
            code=plan_code,
            name=f"Adamjee {plan_name}",
            plan_type=PlanType.FAMILY,
            base_premium=Decimal(str(base_premium)),
            description=description,
            is_active=True,
        )
        db.add(plan)
        db.flush()

        for cov_name, cov_type, limit, copay, cov_desc in COVERAGES:
            db.add(Coverage(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                plan_id=plan.id,
                name=cov_name,
                coverage_type=cov_type,
                limit_amount=Decimal(str(limit)) if limit else None,
                copay=Decimal(str(copay)) if copay is not None else None,
                config={"description": cov_desc},
            ))
