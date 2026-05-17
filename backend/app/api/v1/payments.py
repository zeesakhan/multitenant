from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, get_current_user, require_permissions, get_pagination
from app.schemas.base import APIResponse, PaginatedResponse, PaginationParams
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentListResponse
from app.services.payment_service import PaymentService
from app.services.audit_service import AuditService
from app.constants.permissions import PAYMENT_CREATE, PAYMENT_READ, PAYMENT_READ_ALL

router = APIRouter(tags=["Payments"])


@router.post("/policies/{policy_id}/payments", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
def record_payment(
    policy_id: str,
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(PAYMENT_CREATE)),
):
    service = PaymentService(db, AuditService(db))
    try:
        payment = service.record_payment(tenant.id, policy_id, data, current_user.id)
        db.commit()
        return APIResponse(data=PaymentRead.model_validate(payment))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/policies/{policy_id}/payments", response_model=APIResponse)
def list_policy_payments(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(PAYMENT_READ)),
):
    service = PaymentService(db, AuditService(db))
    payments = service.list_by_policy(tenant.id, policy_id)
    return APIResponse(data=[PaymentRead.model_validate(p) for p in payments])


@router.get("/payments", response_model=PaginatedResponse)
def list_all_payments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    tenant=Depends(require_permissions(PAYMENT_READ_ALL)),
):
    service = PaymentService(db, AuditService(db))
    skip = (pagination.page - 1) * pagination.per_page
    payments, total = service.list_all(tenant.id, skip=skip, limit=pagination.per_page)
    return PaginatedResponse(
        data=[PaymentListResponse.model_validate(p) for p in payments],
        pagination={"page": pagination.page, "per_page": pagination.per_page, "total": total},
    )
