from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, get_current_user, require_permissions, get_pagination
from app.schemas.base import APIResponse, PaginatedResponse, PaginationParams
from app.schemas.member import MemberCreate, MemberUpdate, MemberRead
from app.models.tenant import Tenant
from app.services.member_service import MemberService
from app.services.audit_service import AuditService
from app.constants.permissions import MEMBER_CREATE, MEMBER_READ, MEMBER_UPDATE, MEMBER_DELETE

router = APIRouter(prefix="/applications/{application_id}/members", tags=["Members"])
members_router = APIRouter(prefix="/members", tags=["Members"])


@members_router.get("", response_model=PaginatedResponse)
def list_all_members(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(MEMBER_READ)),
):
    service = MemberService(db, AuditService(db))
    skip = (pagination.page - 1) * pagination.per_page
    members, total = service.list_all(tenant.id, skip=skip, limit=pagination.per_page)
    return PaginatedResponse(
        data=[MemberRead.model_validate(m) for m in members],
        pagination={"page": pagination.page, "per_page": pagination.per_page, "total": total},
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def add_member(
    application_id: str,
    body: MemberCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(MEMBER_CREATE)),
):
    service = MemberService(db, AuditService(db))
    try:
        member = service.add_member(tenant.id, application_id, body, current_user.id)
        db.commit()
        return APIResponse(data=MemberRead.model_validate(member))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=APIResponse)
def list_members(
    application_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(MEMBER_READ)),
):
    service = MemberService(db, AuditService(db))
    members = service.list_members(tenant.id, application_id)
    return APIResponse(data=[MemberRead.model_validate(m) for m in members])


@router.put("/{member_id}", response_model=APIResponse)
def update_member(
    application_id: str,
    member_id: str,
    body: MemberUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(MEMBER_UPDATE)),
):
    service = MemberService(db, AuditService(db))
    try:
        member = service.update_member(tenant.id, member_id, body, current_user.id)
        db.commit()
        return APIResponse(data=MemberRead.model_validate(member))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    application_id: str,
    member_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(MEMBER_DELETE)),
):
    service = MemberService(db, AuditService(db))
    try:
        removed = service.remove_member(tenant.id, member_id, current_user.id)
        if not removed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
