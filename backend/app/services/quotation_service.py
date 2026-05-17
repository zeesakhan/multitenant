from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.product import Quote, Plan, Product
from app.schemas.quotation import QuoteCreate, QuoteUpdate, RateCardCreate, RateCardUpdate
from app.constants.enums import QuoteStatus
from app.utils.formatters import generate_reference_number
from app.services.audit_service import AuditService
from app.services.pricing_service import PricingService
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid


class QuotationService:
    def __init__(self, db: Session, audit_service: AuditService, pricing_service: PricingService):
        self.db = db
        self.audit = audit_service
        self.pricing = pricing_service

    def create_quote(
        self,
        tenant_id: str,
        data: QuoteCreate,
        user_id: str,
        validity_days: int = 30,
    ) -> Quote:
        """Create a new quote for a customer."""
        plan = self.db.query(Plan).filter(
            and_(Plan.tenant_id == tenant_id, Plan.id == data.plan_id)
        ).first()

        if not plan:
            raise ValueError(f"Plan {data.plan_id} not found")

        if plan.product_id != data.product_id:
            raise ValueError("Plan does not belong to specified product")

        quote_number = generate_reference_number("QT")
        valid_until = datetime.now(timezone.utc) + timedelta(days=validity_days)

        total_premium = Decimal(str(plan.base_premium))
        if data.breakdown:
            total_premium = Decimal(str(data.breakdown.get("total", plan.base_premium)))

        quote = Quote(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            quote_number=quote_number,
            product_id=data.product_id,
            plan_id=data.plan_id,
            created_by=user_id,
            customer_email=data.customer_email,
            customer_name=data.customer_name,
            total_premium=total_premium,
            status=QuoteStatus.DRAFT,
            breakdown=data.breakdown,
            valid_until=valid_until,
        )

        self.db.add(quote)
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="create",
            entity_type="quote",
            entity_id=quote.id,
            user_id=user_id,
        )

        return quote

    def get_by_id(self, tenant_id: str, quote_id: str) -> Quote:
        return self.db.query(Quote).filter(
            and_(Quote.tenant_id == tenant_id, Quote.id == quote_id)
        ).first()

    def get_by_number(self, tenant_id: str, quote_number: str) -> Quote:
        return self.db.query(Quote).filter(
            and_(Quote.tenant_id == tenant_id, Quote.quote_number == quote_number)
        ).first()

    def list_quotes(
        self,
        tenant_id: str,
        status: QuoteStatus = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Quote], int]:
        query = self.db.query(Quote).filter(Quote.tenant_id == tenant_id)

        if status:
            query = query.filter(Quote.status == status)

        total = query.count()
        quotes = query.order_by(Quote.created_at.desc()).offset(skip).limit(limit).all()
        return quotes, total

    def update_quote(self, tenant_id: str, quote_id: str, data: QuoteUpdate, user_id: str) -> Quote:
        quote = self.get_by_id(tenant_id, quote_id)
        if not quote:
            return None

        if quote.status != QuoteStatus.DRAFT:
            raise ValueError(f"Cannot update quote in {quote.status} status")

        quote.status = data.status
        if data.breakdown:
            quote.breakdown = data.breakdown

        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="update",
            entity_type="quote",
            entity_id=quote.id,
            user_id=user_id,
            new_values={"status": quote.status},
        )

        return quote

    def send_quote(self, tenant_id: str, quote_id: str, recipient_email: str, user_id: str) -> Quote:
        """Send quote to customer and update status to sent."""
        quote = self.get_by_id(tenant_id, quote_id)
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")

        if quote.status not in [QuoteStatus.DRAFT, QuoteStatus.SENT]:
            raise ValueError(f"Cannot send quote in {quote.status} status")

        quote.status = QuoteStatus.SENT
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="update",
            entity_type="quote",
            entity_id=quote.id,
            user_id=user_id,
            new_values={"status": "sent", "recipient": recipient_email},
        )

        return quote

    def mark_as_viewed(self, tenant_id: str, quote_id: str) -> Quote:
        """Mark quote as viewed by customer."""
        quote = self.get_by_id(tenant_id, quote_id)
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")

        if quote.status == QuoteStatus.SENT:
            quote.status = QuoteStatus.VIEWED
            self.db.flush()

        return quote

    def expire_old_quotes(self, tenant_id: str) -> int:
        """Mark quotes as expired if valid_until has passed."""
        now = datetime.now(timezone.utc)
        expired = self.db.query(Quote).filter(
            and_(
                Quote.tenant_id == tenant_id,
                Quote.status.in_([QuoteStatus.DRAFT, QuoteStatus.SENT, QuoteStatus.VIEWED]),
                Quote.valid_until <= now,
            )
        ).update({"status": QuoteStatus.EXPIRED})

        self.db.flush()
        return expired
