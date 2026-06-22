from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.application import Application, ApplicationItem
from app.models.product import Plan, Quote
from app.models.compliance import PremiumLoading
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationItemCreate, LoadingCreate
from app.constants.enums import ApplicationStatus, QuoteStatus
from app.utils.formatters import generate_reference_number
from app.services.audit_service import AuditService
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
import uuid


class ApplicationService:
    def __init__(self, db: Session, audit_service: AuditService):
        self.db = db
        self.audit = audit_service

    def create_application(
        self,
        tenant_id: str,
        data: ApplicationCreate,
        user_id: str,
    ) -> Application:
        quote = None
        if data.quote_id:
            quote = self.db.query(Quote).filter(
                and_(Quote.tenant_id == tenant_id, Quote.id == data.quote_id)
            ).first()
            if not quote:
                raise ValueError(f"Quote {data.quote_id} not found")

            existing_app = self.db.query(Application).filter(
                and_(Application.tenant_id == tenant_id, Application.quote_id == data.quote_id)
            ).first()
            if existing_app:
                raise ValueError(f"Quote {data.quote_id} already used for application {existing_app.application_number}")

        from app.models.tenant import Tenant
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        last_app = self.db.query(Application).filter(
            Application.tenant_id == tenant_id
        ).order_by(Application.created_at.desc()).first()
        sequence = 1 if not last_app else int(last_app.application_number.split("-")[-1]) + 1

        application_number = generate_reference_number("AP", tenant.code, sequence)
        total_premium = Decimal(str(quote.total_premium)) if quote else Decimal("0.00")

        product_id = data.product_id or (quote.product_id if quote else None)
        plan_id = data.plan_id or (quote.plan_id if quote else None)

        co_pay_dict = data.co_payment_config.model_dump() if data.co_payment_config else None

        application = Application(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            application_number=application_number,
            quote_id=data.quote_id,
            product_id=product_id,
            plan_id=plan_id,
            created_by=user_id,
            customer_email=data.customer_email,
            customer_name=data.customer_name,
            member_count=data.member_count,
            total_premium=total_premium,
            status=ApplicationStatus.DRAFT,
            breakdown=data.breakdown or (quote.breakdown if quote else {}),
            sponsor_type=data.sponsor_type.value if data.sponsor_type else "individual",
            marital_status=data.marital_status,
            occupation=data.occupation,
            employer_name=data.employer_name,
            trn=data.trn,
            is_diplomatic_passport=data.is_diplomatic_passport,
            is_eid_under_process=data.is_eid_under_process,
            existing_health_insurance=data.existing_health_insurance.value if data.existing_health_insurance else None,
            co_payment_config=co_pay_dict,
            cover_amount=data.cover_amount,
        )

        self.db.add(application)
        self.db.flush()

        if data.items:
            for item_data in data.items:
                self._add_item(application.id, tenant_id, item_data)

        self.audit.log(
            tenant_id=tenant_id,
            action="create",
            entity_type="application",
            entity_id=application.id,
            user_id=user_id,
        )

        return application

    def _add_item(self, application_id: str, tenant_id: str, item_data: ApplicationItemCreate) -> ApplicationItem:
        item = ApplicationItem(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            application_id=application_id,
            coverage_id=item_data.coverage_id,
            premium=item_data.premium or Decimal("0.00"),
            status="pending",
            notes=item_data.notes,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def get_by_id(self, tenant_id: str, application_id: str) -> Optional[Application]:
        return self.db.query(Application).filter(
            and_(Application.tenant_id == tenant_id, Application.id == application_id)
        ).first()

    def get_by_number(self, tenant_id: str, application_number: str) -> Optional[Application]:
        return self.db.query(Application).filter(
            and_(Application.tenant_id == tenant_id, Application.application_number == application_number)
        ).first()

    def list_applications(
        self,
        tenant_id: str,
        status: ApplicationStatus = None,
        aml_status: str = None,
        govt_check_status: str = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Application], int]:
        query = self.db.query(Application).filter(Application.tenant_id == tenant_id)

        if status:
            query = query.filter(Application.status == status)
        if aml_status:
            query = query.filter(Application.aml_status == aml_status)
        if govt_check_status:
            query = query.filter(Application.govt_check_status == govt_check_status)

        total = query.count()
        applications = query.order_by(Application.created_at.desc()).offset(skip).limit(limit).all()
        return applications, total

    def update_application(
        self,
        tenant_id: str,
        application_id: str,
        data: ApplicationUpdate,
        user_id: str,
    ) -> Optional[Application]:
        application = self.get_by_id(tenant_id, application_id)
        if not application:
            return None

        if application.status not in (ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED):
            raise ValueError(f"Cannot update application in {application.status} status")

        if data.status is not None:
            application.status = data.status
        if data.breakdown is not None:
            application.breakdown = data.breakdown
        if data.marital_status is not None:
            application.marital_status = data.marital_status
        if data.occupation is not None:
            application.occupation = data.occupation
        if data.employer_name is not None:
            application.employer_name = data.employer_name
        if data.trn is not None:
            application.trn = data.trn
        if data.sponsor_type is not None:
            application.sponsor_type = data.sponsor_type.value
        if data.existing_health_insurance is not None:
            application.existing_health_insurance = data.existing_health_insurance.value
        if data.is_diplomatic_passport is not None:
            application.is_diplomatic_passport = data.is_diplomatic_passport
        if data.is_eid_under_process is not None:
            application.is_eid_under_process = data.is_eid_under_process
        if data.co_payment_config is not None:
            application.co_payment_config = data.co_payment_config.model_dump()
        if data.cover_amount is not None:
            application.cover_amount = data.cover_amount

        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="update",
            entity_type="application",
            entity_id=application.id,
            user_id=user_id,
            new_values={"status": str(application.status)},
        )

        return application

    def submit_application(
        self,
        tenant_id: str,
        application_id: str,
        user_id: str,
    ) -> Application:
        application = self.get_by_id(tenant_id, application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")

        if application.status != ApplicationStatus.DRAFT:
            raise ValueError(f"Can only submit DRAFT applications, current: {application.status}")

        application.status = ApplicationStatus.SUBMITTED
        self.db.flush()

        quote = self.db.query(Quote).filter(Quote.id == application.quote_id).first()
        if quote:
            quote.status = QuoteStatus.CONVERTED
            self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="submit",
            entity_type="application",
            entity_id=application.id,
            user_id=user_id,
            new_values={"status": ApplicationStatus.SUBMITTED},
        )

        return application

    # ── Loadings ─────────────────────────────────────────────────────────────

    def add_loading(
        self,
        tenant_id: str,
        application_id: str,
        data: LoadingCreate,
        user_id: str,
    ) -> PremiumLoading:
        application = self.get_by_id(tenant_id, application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")

        loading = PremiumLoading(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            application_id=application_id,
            member_id=data.member_id,
            loading_type=data.loading_type,
            amount=data.amount,
            percentage=data.percentage,
            applied_by=user_id,
            applied_at=datetime.now(timezone.utc),
            notes=data.notes,
        )
        self.db.add(loading)
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="create",
            entity_type="premium_loading",
            entity_id=loading.id,
            user_id=user_id,
            new_values={
                "loading_type": data.loading_type,
                "amount": str(data.amount) if data.amount else None,
                "percentage": str(data.percentage) if data.percentage else None,
            },
        )

        return loading

    def list_loadings(self, tenant_id: str, application_id: str) -> List[PremiumLoading]:
        return self.db.query(PremiumLoading).filter(
            and_(
                PremiumLoading.tenant_id == tenant_id,
                PremiumLoading.application_id == application_id,
            )
        ).order_by(PremiumLoading.applied_at).all()

    def remove_loading(
        self,
        tenant_id: str,
        application_id: str,
        loading_id: str,
        user_id: str,
    ) -> bool:
        loading = self.db.query(PremiumLoading).filter(
            and_(
                PremiumLoading.tenant_id == tenant_id,
                PremiumLoading.application_id == application_id,
                PremiumLoading.id == loading_id,
            )
        ).first()

        if not loading:
            return False

        self.db.delete(loading)
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="delete",
            entity_type="premium_loading",
            entity_id=loading_id,
            user_id=user_id,
        )

        return True

    # ── Remarks ───────────────────────────────────────────────────────────────

    def add_remark(
        self,
        tenant_id: str,
        application_id: str,
        text: str,
        author_id: str,
        author_name: str,
        author_role: str,
    ) -> dict:
        application = self.get_by_id(tenant_id, application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")

        remark = {
            "id": str(uuid.uuid4()),
            "author_id": author_id,
            "author_name": author_name,
            "author_role": author_role,
            "text": text,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        remarks = list(application.remarks or [])
        remarks.append(remark)
        application.remarks = remarks
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="create",
            entity_type="remark",
            entity_id=remark["id"],
            user_id=author_id,
        )

        return remark

    def get_remarks(self, tenant_id: str, application_id: str) -> list:
        application = self.get_by_id(tenant_id, application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        return application.remarks or []

    # ── Premium recalculation ─────────────────────────────────────────────────

    def recalculate_premium(
        self,
        tenant_id: str,
        application_id: str,
        user_id: str,
    ) -> Application:
        """Recalculate full breakdown using current members and loadings; persist to premium_breakdown."""
        from app.services.pricing_service import PricingService
        from app.models.member import Member
        from datetime import date as dt_date

        application = self.get_by_id(tenant_id, application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        if not application.plan_id or not application.product_id:
            raise ValueError("Application must have plan_id and product_id to recalculate")

        members = self.db.query(Member).filter(
            and_(Member.tenant_id == tenant_id, Member.application_id == application_id)
        ).all()

        def age(dob):
            today = dt_date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        members_factors = [
            {
                "member_id": m.id,
                "age": age(m.date_of_birth),
                "gender": m.gender if isinstance(m.gender, str) else m.gender.value,
                "location": "Dubai",
                "sum_insured": float(application.cover_amount) if application.cover_amount else 1_000_000,
            }
            for m in members
        ] or [{"age": 30, "gender": "male", "location": "Dubai", "sum_insured": 1_000_000}]

        svc = PricingService(self.db)
        breakdown = svc.calculate_full_breakdown(
            tenant_id=tenant_id,
            product_id=application.product_id,
            plan_id=application.plan_id,
            members_factors=members_factors,
            application_id=application_id,
        )

        def _serialise(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            if isinstance(obj, list):
                return [_serialise(i) for i in obj]
            if isinstance(obj, dict):
                return {k: _serialise(v) for k, v in obj.items()}
            return obj

        application.premium_breakdown = _serialise(breakdown)
        application.total_premium = breakdown["amount_payable"]
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="recalculate_premium",
            entity_type="application",
            entity_id=application.id,
            user_id=user_id,
            new_values={"total_premium": str(breakdown["amount_payable"])},
        )

        return application

    # ── Items ─────────────────────────────────────────────────────────────────

    def get_items(self, tenant_id: str, application_id: str) -> list[ApplicationItem]:
        return self.db.query(ApplicationItem).filter(
            and_(
                ApplicationItem.tenant_id == tenant_id,
                ApplicationItem.application_id == application_id,
            )
        ).all()

    def add_item(
        self,
        tenant_id: str,
        application_id: str,
        data: ApplicationItemCreate,
        user_id: str,
    ) -> ApplicationItem:
        application = self.get_by_id(tenant_id, application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")

        if application.status != ApplicationStatus.DRAFT:
            raise ValueError("Can only add items to DRAFT applications")

        item = self._add_item(application_id, tenant_id, data)

        self.audit.log(
            tenant_id=tenant_id,
            action="create",
            entity_type="application_item",
            entity_id=item.id,
            user_id=user_id,
        )

        return item

    def remove_item(
        self,
        tenant_id: str,
        item_id: str,
        user_id: str,
    ) -> bool:
        item = self.db.query(ApplicationItem).filter(
            and_(ApplicationItem.tenant_id == tenant_id, ApplicationItem.id == item_id)
        ).first()

        if not item:
            return False

        application = self.get_by_id(tenant_id, item.application_id)
        if application.status != ApplicationStatus.DRAFT:
            raise ValueError("Can only remove items from DRAFT applications")

        self.db.delete(item)
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="delete",
            entity_type="application_item",
            entity_id=item_id,
            user_id=user_id,
        )

        return True

    # ── Approve / Reject ──────────────────────────────────────────────────────

    def approve_application(
        self,
        tenant_id: str,
        application_id: str,
        user_id: str,
    ) -> Application:
        application = self.get_by_id(tenant_id, application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")

        application.status = ApplicationStatus.APPROVED
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="approve",
            entity_type="application",
            entity_id=application.id,
            user_id=user_id,
            new_values={"status": ApplicationStatus.APPROVED},
        )

        return application

    def reject_application(
        self,
        tenant_id: str,
        application_id: str,
        reason: str,
        user_id: str,
    ) -> Application:
        application = self.get_by_id(tenant_id, application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")

        application.status = ApplicationStatus.REJECTED
        if not application.additional_info:
            application.additional_info = {}
        application.additional_info["rejection_reason"] = reason
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="reject",
            entity_type="application",
            entity_id=application.id,
            user_id=user_id,
            new_values={"status": ApplicationStatus.REJECTED, "rejection_reason": reason},
        )

        return application
