from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, get_current_user, require_permissions, get_pagination
from app.schemas.base import APIResponse, PaginatedResponse, PaginationParams
from app.schemas.quotation import QuoteCreate, QuoteUpdate, QuoteRead, QuoteSendRequest, QuoteListResponse, RateCardCreate, RateCardRead
from app.models.tenant import Tenant
from app.models.product import RateCard
from app.services.quotation_service import QuotationService
from app.services.pricing_service import PricingService
from app.services.audit_service import AuditService
from app.constants.permissions import QUOTATION_CREATE, QUOTATION_READ, QUOTATION_UPDATE, QUOTATION_SEND, RATE_CARD_CREATE, RATE_CARD_READ
import uuid

router = APIRouter(prefix="/quotations", tags=["Quotations"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def create_quote(
    body: QuoteCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(QUOTATION_CREATE)),
):
    """Create a new quote."""
    audit_service = AuditService(db)
    pricing_service = PricingService(db)
    quotation_service = QuotationService(db, audit_service, pricing_service)

    try:
        quote = quotation_service.create_quote(tenant.id, body, current_user.id)
        db.commit()
        return APIResponse(data=QuoteRead.model_validate(quote))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=PaginatedResponse)
def list_quotes(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    tenant: Tenant = Depends(require_permissions(QUOTATION_READ)),
):
    """List all quotes for the current tenant."""
    audit_service = AuditService(db)
    pricing_service = PricingService(db)
    quotation_service = QuotationService(db, audit_service, pricing_service)

    skip = (pagination.page - 1) * pagination.per_page
    quotes, total = quotation_service.list_quotes(tenant.id, skip=skip, limit=pagination.per_page)

    return PaginatedResponse(
        data=[QuoteListResponse.model_validate(q) for q in quotes],
        pagination={
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": total,
        }
    )


@router.get("/{quote_id}", response_model=APIResponse)
def get_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(QUOTATION_READ)),
):
    """Get quote details."""
    audit_service = AuditService(db)
    pricing_service = PricingService(db)
    quotation_service = QuotationService(db, audit_service, pricing_service)

    quote = quotation_service.get_by_id(tenant.id, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")

    return APIResponse(data=QuoteRead.model_validate(quote))


@router.put("/{quote_id}", response_model=APIResponse)
def update_quote(
    quote_id: str,
    body: QuoteUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(QUOTATION_UPDATE)),
):
    """Update quote details."""
    audit_service = AuditService(db)
    pricing_service = PricingService(db)
    quotation_service = QuotationService(db, audit_service, pricing_service)

    try:
        quote = quotation_service.update_quote(tenant.id, quote_id, body, current_user.id)
        if not quote:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
        db.commit()
        return APIResponse(data=QuoteRead.model_validate(quote))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{quote_id}/send", response_model=APIResponse)
def send_quote(
    quote_id: str,
    body: QuoteSendRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(QUOTATION_SEND)),
):
    """Send quote to customer."""
    audit_service = AuditService(db)
    pricing_service = PricingService(db)
    quotation_service = QuotationService(db, audit_service, pricing_service)

    quote = quotation_service.get_by_id(tenant.id, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")

    recipient_email = body.recipient_email or quote.customer_email

    try:
        quote = quotation_service.send_quote(tenant.id, quote_id, recipient_email, current_user.id)
        db.commit()
        return APIResponse(data=QuoteRead.model_validate(quote))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{quote_id}/mark-viewed", response_model=APIResponse)
def mark_quote_viewed(
    quote_id: str,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(require_permissions(QUOTATION_READ)),
):
    """Mark quote as viewed by customer."""
    audit_service = AuditService(db)
    pricing_service = PricingService(db)
    quotation_service = QuotationService(db, audit_service, pricing_service)

    try:
        quote = quotation_service.mark_as_viewed(tenant.id, quote_id)
        db.commit()
        return APIResponse(data=QuoteRead.model_validate(quote))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/rate-cards", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def create_rate_card(
    body: RateCardCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(RATE_CARD_CREATE)),
):
    """Create a new rate card."""
    rate_card = RateCard(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        product_id=body.product_id,
        plan_id=body.plan_id,
        effective_date=body.effective_date,
        expiry_date=body.expiry_date,
        rates=body.rates,
    )
    db.add(rate_card)
    db.commit()

    return APIResponse(data=RateCardRead.model_validate(rate_card))


@router.get("/rate-cards/{rate_card_id}", response_model=APIResponse)
def get_rate_card(
    rate_card_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(RATE_CARD_READ)),
):
    """Get rate card details."""
    rate_card = db.query(RateCard).filter(
        RateCard.tenant_id == tenant.id,
        RateCard.id == rate_card_id
    ).first()

    if not rate_card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate card not found")

    return APIResponse(data=RateCardRead.model_validate(rate_card))
