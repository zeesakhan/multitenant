from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, get_current_user, require_permissions, get_pagination
from app.schemas.base import APIResponse, PaginatedResponse, PaginationParams
from app.schemas.claim import ClaimCreate, ClaimUpdate, ClaimReview, ClaimRead, ClaimListResponse
from app.services.claim_service import ClaimService
from app.services.audit_service import AuditService
from app.constants.permissions import (
    CLAIM_CREATE, CLAIM_READ, CLAIM_READ_ALL, CLAIM_UPDATE, CLAIM_APPROVE, CLAIM_REJECT, CLAIM_PAY,
)
from pydantic import BaseModel

router = APIRouter(prefix="/claims", tags=["Claims"])


class RejectBody(BaseModel):
    reason: str


@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
def create_claim(
    data: ClaimCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(CLAIM_CREATE)),
):
    service = ClaimService(db, AuditService(db))
    try:
        claim = service.create(tenant.id, data, current_user.id)
        db.commit()
        return APIResponse(data=ClaimRead.model_validate(claim))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=PaginatedResponse)
def list_claims(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    tenant=Depends(require_permissions(CLAIM_READ_ALL)),
):
    service = ClaimService(db, AuditService(db))
    skip = (pagination.page - 1) * pagination.per_page
    claims, total = service.list_all(tenant.id, skip=skip, limit=pagination.per_page)
    return PaginatedResponse(
        data=[ClaimListResponse.model_validate(c) for c in claims],
        pagination={"page": pagination.page, "per_page": pagination.per_page, "total": total},
    )


@router.get("/{claim_id}", response_model=APIResponse)
def get_claim(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(CLAIM_READ)),
):
    service = ClaimService(db, AuditService(db))
    claim = service.get(tenant.id, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return APIResponse(data=ClaimRead.model_validate(claim))


@router.put("/{claim_id}", response_model=APIResponse)
def update_claim(
    claim_id: str,
    data: ClaimUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(CLAIM_UPDATE)),
):
    service = ClaimService(db, AuditService(db))
    try:
        claim = service.update(tenant.id, claim_id, data, current_user.id)
        db.commit()
        return APIResponse(data=ClaimRead.model_validate(claim))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{claim_id}/review", response_model=APIResponse)
def start_review(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(CLAIM_APPROVE)),
):
    service = ClaimService(db, AuditService(db))
    try:
        claim = service.start_review(tenant.id, claim_id, current_user.id)
        db.commit()
        return APIResponse(data=ClaimRead.model_validate(claim))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{claim_id}/approve", response_model=APIResponse)
def approve_claim(
    claim_id: str,
    data: ClaimReview,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(CLAIM_APPROVE)),
):
    service = ClaimService(db, AuditService(db))
    try:
        claim = service.approve(tenant.id, claim_id, data, current_user.id)
        db.commit()
        return APIResponse(data=ClaimRead.model_validate(claim))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{claim_id}/reject", response_model=APIResponse)
def reject_claim(
    claim_id: str,
    data: RejectBody,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(CLAIM_REJECT)),
):
    service = ClaimService(db, AuditService(db))
    try:
        claim = service.reject(tenant.id, claim_id, data.reason, current_user.id)
        db.commit()
        return APIResponse(data=ClaimRead.model_validate(claim))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{claim_id}/pay", response_model=APIResponse)
def pay_claim(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(CLAIM_PAY)),
):
    service = ClaimService(db, AuditService(db))
    try:
        claim = service.mark_paid(tenant.id, claim_id, current_user.id)
        db.commit()
        return APIResponse(data=ClaimRead.model_validate(claim))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
