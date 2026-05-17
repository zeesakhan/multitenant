from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.application import Application, ApplicationItem
from app.models.product import Plan, Quote
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationItemCreate
from app.constants.enums import ApplicationStatus, QuoteStatus
from app.utils.formatters import generate_reference_number
from app.services.audit_service import AuditService
from datetime import datetime, timezone
from decimal import Decimal
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
        """Create a new application, optionally linked to a quote."""
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
                raise ValueError(f"Quote {data.quote_id} has already been used for application {existing_app.application_number}")

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

        # Resolve plan/product: prefer explicit fields, fall back to quote
        product_id = data.product_id or (quote.product_id if quote else None)
        plan_id = data.plan_id or (quote.plan_id if quote else None)

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
        )

        self.db.add(application)
        self.db.flush()

        # Add initial items if provided
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
        """Internal method to add an application item."""
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

    def get_by_id(self, tenant_id: str, application_id: str) -> Application:
        return self.db.query(Application).filter(
            and_(Application.tenant_id == tenant_id, Application.id == application_id)
        ).first()

    def get_by_number(self, tenant_id: str, application_number: str) -> Application:
        return self.db.query(Application).filter(
            and_(Application.tenant_id == tenant_id, Application.application_number == application_number)
        ).first()

    def list_applications(
        self,
        tenant_id: str,
        status: ApplicationStatus = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Application], int]:
        query = self.db.query(Application).filter(Application.tenant_id == tenant_id)

        if status:
            query = query.filter(Application.status == status)

        total = query.count()
        applications = query.order_by(Application.created_at.desc()).offset(skip).limit(limit).all()
        return applications, total

    def update_application(
        self,
        tenant_id: str,
        application_id: str,
        data: ApplicationUpdate,
        user_id: str,
    ) -> Application:
        application = self.get_by_id(tenant_id, application_id)
        if not application:
            return None

        if application.status != ApplicationStatus.DRAFT:
            raise ValueError(f"Cannot update application in {application.status} status")

        if data.status is not None:
            application.status = data.status
        if data.breakdown is not None:
            application.breakdown = data.breakdown

        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="update",
            entity_type="application",
            entity_id=application.id,
            user_id=user_id,
            new_values={"status": application.status},
        )

        return application

    def submit_application(
        self,
        tenant_id: str,
        application_id: str,
        user_id: str,
    ) -> Application:
        """Submit application for underwriting."""
        application = self.get_by_id(tenant_id, application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")

        if application.status != ApplicationStatus.DRAFT:
            raise ValueError(f"Can only submit applications in DRAFT status, current: {application.status}")

        application.status = ApplicationStatus.SUBMITTED
        self.db.flush()

        # Update quote status to CONVERTED
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
        """Add item to application."""
        application = self.get_by_id(tenant_id, application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")

        if application.status != ApplicationStatus.DRAFT:
            raise ValueError(f"Can only add items to applications in DRAFT status")

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
        """Remove item from application."""
        item = self.db.query(ApplicationItem).filter(
            and_(ApplicationItem.tenant_id == tenant_id, ApplicationItem.id == item_id)
        ).first()

        if not item:
            return False

        application = self.get_by_id(tenant_id, item.application_id)
        if application.status != ApplicationStatus.DRAFT:
            raise ValueError(f"Can only remove items from applications in DRAFT status")

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

    def approve_application(
        self,
        tenant_id: str,
        application_id: str,
        user_id: str,
    ) -> Application:
        """Approve application (underwriter action)."""
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
        """Reject application (underwriter action)."""
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
