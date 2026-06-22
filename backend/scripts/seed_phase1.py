"""Phase 1 seed: Adamjee tenant with spec-correct 10 plans, market_configs,
commission_configs, rate_cards, and staff users.

Run from backend/:
    DATABASE_URL=postgresql://zeeshankhan@localhost:5432/health_insurance \
    python scripts/seed_phase1.py

Safe to re-run: idempotent checks throughout.
"""
import os, sys, uuid
from decimal import Decimal
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all models so SQLAlchemy mapper resolves all relationships
import app.models.tenant
import app.models.user
import app.models.audit
import app.models.application
import app.models.member
import app.models.product
import app.models.policy
import app.models.payment
import app.models.claim
import app.models.document
import app.models.workflow
import app.models.market_config
import app.models.compliance

from passlib.context import CryptContext
from app.db.database import _get_session_factory
from app.models.tenant import Tenant, BrandConfig
from app.models.user import User
from app.models.product import Product, Plan, Coverage, RateCard
from app.models.market_config import MarketConfig
from app.models.compliance import CommissionConfig
from app.constants.enums import (
    TenantStatus, UserType, UserStatus, ProductStatus, PlanType, CoverageType,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def uid(): return str(uuid.uuid4())
def hp(pw): return pwd_context.hash(pw)


db = _get_session_factory()()

try:
    # ── 1. Adamjee Tenant ─────────────────────────────────────────────────────
    tenant = db.query(Tenant).filter(Tenant.code == "ADAMJEE").first()

    if not tenant:
        print("Creating ADAMJEE tenant...")
        tenant = Tenant(
            id=uid(),
            code="ADAMJEE",
            name="Adamjee Insurance Company Limited — Dubai Branch",
            status=TenantStatus.ACTIVE,
            currency="AED",
            timezone="Asia/Dubai",
            config={
                "country": "UAE",
                "regulator": "Insurance Authority (IA) UAE / CBUAE",
                "reinsurer": "Munich RE",
                "dha_compliant": True,
                "support_phone": "+971-4-XXX-XXXX",
                "support_email": "customercare@adamjeeinsurance.ae",
                "website": "https://adamjeeinsurance.ae",
            },
        )
        db.add(tenant)
        db.flush()

        db.add(BrandConfig(
            id=uid(),
            tenant_id=tenant.id,
            company_name="Adamjee Insurance",
            tagline="Your Trusted Insurance Partner in the UAE",
            primary_color="#0055A5",
            secondary_color="#F59E0B",
            support_email="customercare@adamjeeinsurance.ae",
            support_phone="+971-4-XXX-XXXX",
        ))
        db.flush()
        print(f"  + Adamjee tenant created: {tenant.id}")
    else:
        print(f"Found existing ADAMJEE tenant: {tenant.id}")

    tid = tenant.id

    # ── 2. Staff Users ────────────────────────────────────────────────────────
    USERS = [
        ("admin@adamjee.ae",         hp("adamjee123"), "Adamjee",  "Admin",         UserType.TENANT_ADMIN),
        ("underwriter@adamjee.ae",   hp("adamjee123"), "Reem",     "Al-Mansouri",   UserType.UNDERWRITER),
        ("broker@adamjee.ae",        hp("adamjee123"), "Khalid",   "Al-Rashidi",    UserType.BROKER),
        ("compliance@adamjee.ae",    hp("adamjee123"), "Fatima",   "Al-Hashemi",    UserType.COMPLIANCE_OFFICER),
        ("finance@adamjee.ae",       hp("adamjee123"), "Ahmed",    "Al-Suwaidi",    UserType.FINANCE),
    ]

    for email, pw_hash, first, last, utype in USERS:
        existing = db.query(User).filter(User.tenant_id == tid, User.email == email).first()
        if not existing:
            db.add(User(
                id=uid(), tenant_id=tid, email=email, password_hash=pw_hash,
                first_name=first, last_name=last,
                user_type=utype, status=UserStatus.ACTIVE,
            ))
            print(f"  + user: {email}")
        else:
            print(f"  ~ user exists: {email}")

    db.flush()

    # ── 3. Adamjee DHA Family Care Product ────────────────────────────────────
    product = db.query(Product).filter(
        Product.tenant_id == tid, Product.code == "ADJ-HEALTH"
    ).first()

    if not product:
        product = Product(
            id=uid(),
            tenant_id=tid,
            code="ADJ-HEALTH",
            name="Adamjee DHA Health Insurance",
            description=(
                "DHA-compliant group and individual health insurance for UAE residents. "
                "Annual aggregate limit up to AED 1,000,000 per person. "
                "Dual TPA network: MEDNET and NAS. 10 plan tiers."
            ),
            status=ProductStatus.ACTIVE,
        )
        db.add(product)
        db.flush()
        print(f"  + product: {product.name}")
    else:
        print(f"  ~ product exists: {product.name}")

    # ── 4. Plans (spec-exact 10 tiers) ───────────────────────────────────────
    # base_premium = annual AED per person, reference: age 26-35, male, Dubai, AED 1M cover
    # Source: session prompt section 3.8 (demo-observed, all configurable)
    PLAN_TIERS = [
        ("Workers Network",       "ADJ-WN",     6340.00, "NAS-WN",          "NAS – WN (OP restricted to Clinics). Lowest cost option."),
        ("Silk Road",             "ADJ-SR",     6823.00, "MEDNET Silk Road", "MEDNET Silk Road network. DHA Essential Benefits Plan compliant."),
        ("Pearl",                 "ADJ-PL",     7340.00, "MEDNET Pearl",     "MEDNET Pearl network. Mid-entry tier with solid clinic access."),
        ("Super Restricted Network", "ADJ-SRN", 8398.00, "NAS-SRN",         "NAS Super Restricted Network. Curated hospital and clinic list."),
        ("Emerald",               "ADJ-EM",     8601.00, "MEDNET Emerald",   "MEDNET Emerald network. Comprehensive mid-tier private hospital access."),
        ("Green",                 "ADJ-GN",    10196.00, "MEDNET Green",     "MEDNET Green network. Excellent private hospital and clinic coverage."),
        ("Restricted Network",    "ADJ-RN",    10769.00, "NAS-RN",          "NAS Restricted Network. Strong coverage with wide UAE clinic access."),
        ("Silver Classic",        "ADJ-SC",    11660.00, "MEDNET Silver Classic", "MEDNET Silver Classic. Premium tier with top private hospitals."),
        ("Silver Premium",        "ADJ-SP",    11882.00, "MEDNET Silver Premium", "MEDNET Silver Premium. Enhanced Silver tier with extended benefits."),
        ("General Network",       "ADJ-GEN",   16757.00, "NAS-GN",          "NAS General Network. Comprehensive access including international cover."),
    ]

    COVERAGES = [
        # (name, coverage_type, limit_amount, copay_pct, config_desc)
        ("Inpatient Hospitalization",  CoverageType.HOSPITALIZATION, 1_000_000, 0.0,  "Private room, ICU, surgeon & anaesthetist fees, organ transplant. Sub-limit = annual limit."),
        ("Outpatient Consultation",    CoverageType.OUTPATIENT,      None,      20.0, "GP & specialist visits. Co-pay: 20% (max AED 50 per visit)."),
        ("Diagnostics & Lab Tests",    CoverageType.OUTPATIENT,      None,       0.0, "All lab tests and diagnostics. 0% co-pay."),
        ("Pharmaceuticals",            CoverageType.PRESCRIPTION,    None,       0.0, "Prescribed medications per DHA formulary. 0% co-pay."),
        ("Dental",                     CoverageType.DENTAL,         3_500,      20.0, "Annual sub-limit AED 3,500. 20% co-pay."),
        ("Maternity",                  CoverageType.MATERNITY,      10_000,      0.0, "Normal & caesarean delivery. AED 10,000 per event. Newborn first 30 days covered."),
        ("Physiotherapy",              CoverageType.WELLNESS,        None,        0.0, "Up to 15 sessions per year. 0% co-pay."),
        ("Alternative Medicine",       CoverageType.WELLNESS,       1_600,       0.0, "Homeopathy, chiropractic, acupuncture — AED 1,600/year."),
        ("Mental Health",              CoverageType.MENTAL_HEALTH,  None,        0.0, "Emergency mental health treatments covered."),
        ("Vaccination",                CoverageType.PREVENTIVE,     None,        0.0, "All vaccinations per UAE MOH immunisation schedule."),
        ("Pre-existing Conditions",    CoverageType.HOSPITALIZATION,150_000,     0.0, "Declared chronic & pre-existing conditions. Sub-limit AED 150,000."),
        ("Ambulance",                  CoverageType.EMERGENCY,      None,        0.0, "Emergency ambulance with hospital admission."),
        ("Repatriation",               CoverageType.EMERGENCY,      7_500,       0.0, "Repatriation of mortal remains up to AED 7,500."),
    ]

    plan_ids = []

    for plan_name, plan_code, base_premium, tpa_name, description in PLAN_TIERS:
        existing_plan = db.query(Plan).filter(
            Plan.tenant_id == tid, Plan.code == plan_code
        ).first()

        if not existing_plan:
            plan = Plan(
                id=uid(),
                tenant_id=tid,
                product_id=product.id,
                code=plan_code,
                name=plan_name,
                plan_type=PlanType.INDIVIDUAL,
                base_premium=Decimal(str(base_premium)),
                description=description,
                is_active=True,
                coverage_details={"tpa": tpa_name, "annual_limit_aed": 1_000_000},
            )
            db.add(plan)
            db.flush()

            for cov_name, cov_type, limit, copay, cov_desc in COVERAGES:
                db.add(Coverage(
                    id=uid(),
                    tenant_id=tid,
                    plan_id=plan.id,
                    name=cov_name,
                    coverage_type=cov_type,
                    limit_amount=Decimal(str(limit)) if limit else None,
                    copay=Decimal(str(copay)) if copay is not None else Decimal("0"),
                    coinsurance_percent=Decimal("0"),
                    config={"description": cov_desc, "tpa": tpa_name},
                ))

            print(f"  + plan: {plan_name} (AED {base_premium:,.0f}/yr)")
            plan_ids.append(plan.id)
        else:
            print(f"  ~ plan exists: {plan_name}")
            plan_ids.append(existing_plan.id)

    db.flush()

    # ── 5. Rate Cards ─────────────────────────────────────────────────────────
    # Age/gender rating factors relative to reference: age 26-35, male = 1.00
    RATE_CARD_RATES = {
        "age_factors": {
            "0-17":  0.55, "18-25": 0.80, "26-35": 1.00, "36-45": 1.25,
            "46-55": 1.60, "56-60": 2.00, "61-65": 2.50, "66-70": 3.10, "71-80": 3.80,
        },
        "gender_factors": {
            "male": 1.00, "female": 1.05, "other": 1.00, "prefer_not_to_say": 1.00,
        },
        "location_factors": {
            "Dubai": 1.05, "Abu Dhabi": 1.00, "Sharjah": 0.98, "Ajman": 0.97,
            "Ras Al Khaimah": 0.96, "Fujairah": 0.96, "Umm Al Quwain": 0.95,
        },
        "sum_insured_factors": {
            "150000":    0.72,
            "500000":    0.88,
            "1000000":   1.00,
            "5000000":   1.40,
            "unlimited": 1.85,
        },
    }

    eff_from = date.today()
    eff_to = date(eff_from.year + 1, eff_from.month, eff_from.day)

    all_plans = db.query(Plan).filter(Plan.tenant_id == tid).all()
    for plan in all_plans:
        existing_rc = db.query(RateCard).filter(
            RateCard.tenant_id == tid,
            RateCard.plan_id == plan.id,
            RateCard.effective_date <= eff_from,
            RateCard.expiry_date > eff_from,
        ).first()
        if not existing_rc:
            db.add(RateCard(
                id=uid(),
                tenant_id=tid,
                product_id=plan.product_id,
                plan_id=plan.id,
                effective_date=eff_from,
                expiry_date=eff_to,
                rates=RATE_CARD_RATES,
            ))
            print(f"  + rate_card: {plan.name}")
        else:
            print(f"  ~ rate_card exists: {plan.name}")

    db.flush()

    # ── 6. Market Configs ─────────────────────────────────────────────────────
    MARKET_CONFIGS = [
        ("vat_rate",                    0.05,       "UAE VAT rate (5%)"),
        ("psp_fee",                     24.00,      "PSP processing fee per policy (AED)"),
        ("icp_fee",                     50.00,      "ICP fee per policy (AED, configurable)"),
        ("quote_validity_days",         30,         "Days a quote remains valid"),
        ("aml_edd_threshold",           50000,      "Premium threshold (AED) triggering Enhanced Due Diligence"),
        ("session_timeout_minutes",     30,         "Session inactivity timeout (minutes)"),
        ("default_annual_limit",        1000000,    "Default annual medical cover limit (AED)"),
        ("audit_log_retention_years",   7,          "Audit log retention (years, regulatory minimum)"),
        ("policy_doc_retention_years",  10,         "Policy document retention (years, regulatory minimum)"),
        ("str_retention_years",         10,         "STR record retention (years, regulatory minimum)"),
        # AML risk scoring weights
        ("aml_pep_self_score",          25,         "AML risk points: member is a PEP"),
        ("aml_pep_related_score",       15,         "AML risk points: member is related to a PEP"),
        ("aml_fatf_score",              15,         "AML risk points: FATF high-risk nationality"),
        ("aml_cash_score",              10,         "AML risk points: cash payment method"),
        ("aml_occupation_score",        5,          "AML risk points: high-risk occupation"),
        ("aml_diplomatic_score",        5,          "AML risk points: diplomatic passport holder"),
        ("aml_prior_flag_score",        20,         "AML risk points: prior AML flag on record"),
        ("aml_premium_over_threshold",  10,         "AML risk points: premium exceeds EDD threshold"),
        # AML risk bands
        ("aml_low_max",                 25,         "AML risk band: 0–N = LOW (auto-proceed)"),
        ("aml_medium_max",              50,         "AML risk band: N+1–M = MEDIUM (notify Compliance Officer)"),
        ("aml_high_max",                75,         "AML risk band: M+1–P = HIGH (AML Hold)"),
        # Default co-payment
        ("default_opt_copay_pct",       20.0,       "Default OPT co-pay percentage"),
        ("default_opt_copay_cap_aed",   50.0,       "Default OPT co-pay cap per visit (AED)"),
        ("default_pharmacy_copay",      0.0,        "Default pharmacy co-pay percentage"),
        ("default_lab_copay",           0.0,        "Default laboratory co-pay percentage"),
        ("default_physio_copay",        0.0,        "Default physiotherapy co-pay percentage"),
        # Identifiers
        ("currency",                    "AED",      "Reporting currency"),
        ("insurer_name",                "Adamjee Insurance Company Limited — Dubai Branch", "Legal insurer name"),
        ("reinsurer_name",              "Munich RE","Reinsurer name"),
        ("tpa_primary",                 "MEDNET",   "Primary TPA partner"),
        ("tpa_secondary",               "NAS",      "Secondary TPA partner"),
        ("regulator",                   "Insurance Authority (IA) UAE / CBUAE", "Primary regulator"),
        ("dha_compliant",               True,       "Platform is DHA-compliant for Dubai"),
        ("aml_framework",               "CBUAE Notice 2021/6; UAE Cabinet Resolution No. 74 of 2020", "AML regulatory framework"),
    ]

    for key, value, description in MARKET_CONFIGS:
        existing_mc = db.query(MarketConfig).filter(
            MarketConfig.tenant_id == tid, MarketConfig.key == key
        ).first()
        if not existing_mc:
            db.add(MarketConfig(
                id=uid(), tenant_id=tid, key=key, value=value, description=description,
            ))
            print(f"  + market_config: {key}")
        else:
            print(f"  ~ market_config exists: {key}")

    db.flush()

    # ── 7. Commission Config (default, tenant-wide) ────────────────────────────
    existing_comm = db.query(CommissionConfig).filter(
        CommissionConfig.tenant_id == tid,
        CommissionConfig.broker_id.is_(None),
        CommissionConfig.plan_id.is_(None),
    ).first()

    if not existing_comm:
        db.add(CommissionConfig(
            id=uid(),
            tenant_id=tid,
            broker_id=None,
            plan_id=None,
            insurer_pct=Decimal("5.00"),
            broker_pct=Decimal("15.50"),
            tpa_pct=Decimal("0.00"),
        ))
        print("  + commission_config: default (insurer 5%, broker 15.5%)")
    else:
        print("  ~ commission_config: default exists")

    db.commit()
    print("\nPhase 1 seed complete.")
    print("\nDemo credentials for ADAMJEE tenant:")
    print("  Tenant code: ADAMJEE")
    print("  Admin:       admin@adamjee.ae / adamjee123")
    print("  Underwriter: underwriter@adamjee.ae / adamjee123")
    print("  Broker:      broker@adamjee.ae / adamjee123")
    print("  Compliance:  compliance@adamjee.ae / adamjee123")
    print("  Finance:     finance@adamjee.ae / adamjee123")

except Exception as e:
    db.rollback()
    print(f"ERROR: {e}")
    raise
finally:
    db.close()
