from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, get_current_user, require_permissions, get_pagination
from app.schemas.base import APIResponse, PaginatedResponse, PaginationParams
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationRead, ApplicationListResponse,
    ApplicationItemCreate, ApplicationItemRead, ApplicationSubmitRequest,
    LoadingCreate, LoadingRead, RemarkCreate,
)
from app.models.tenant import Tenant
from app.services.application_service import ApplicationService
from app.services.policy_service import PolicyService
from app.services.audit_service import AuditService
from app.schemas.policy import PolicyRead
from app.constants.permissions import (
    APPLICATION_CREATE, APPLICATION_READ, APPLICATION_UPDATE,
    APPLICATION_SUBMIT, APPLICATION_APPROVE, APPLICATION_REJECT, POLICY_ISSUE,
    LOADING_APPLY, LOADING_READ,
)

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def create_application(
    body: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(APPLICATION_CREATE)),
):
    audit_service = AuditService(db)
    service = ApplicationService(db, audit_service)
    try:
        application = service.create_application(tenant.id, body, current_user.id)
        db.commit()
        return APIResponse(data=ApplicationRead.model_validate(application))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=PaginatedResponse)
def list_applications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    status_filter: str = None,
    aml_status: str = None,
    govt_check_status: str = None,
    pagination: PaginationParams = Depends(get_pagination),
    tenant: Tenant = Depends(require_permissions(APPLICATION_READ)),
):
    service = ApplicationService(db, AuditService(db))
    skip = (pagination.page - 1) * pagination.per_page
    applications, total = service.list_applications(
        tenant.id,
        status=status_filter,
        aml_status=aml_status,
        govt_check_status=govt_check_status,
        skip=skip,
        limit=pagination.per_page,
    )
    return PaginatedResponse(
        data=[ApplicationListResponse.model_validate(a) for a in applications],
        pagination={"page": pagination.page, "per_page": pagination.per_page, "total": total},
    )


@router.get("/{application_id}", response_model=APIResponse)
def get_application(
    application_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(APPLICATION_READ)),
):
    service = ApplicationService(db, AuditService(db))
    application = service.get_by_id(tenant.id, application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return APIResponse(data=ApplicationRead.model_validate(application))


@router.put("/{application_id}", response_model=APIResponse)
def update_application(
    application_id: str,
    body: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(APPLICATION_UPDATE)),
):
    audit_service = AuditService(db)
    service = ApplicationService(db, audit_service)
    try:
        application = service.update_application(tenant.id, application_id, body, current_user.id)
        if not application:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        db.commit()
        return APIResponse(data=ApplicationRead.model_validate(application))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{application_id}/submit", response_model=APIResponse)
def submit_application(
    application_id: str,
    body: ApplicationSubmitRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(APPLICATION_SUBMIT)),
):
    audit_service = AuditService(db)
    service = ApplicationService(db, audit_service)
    try:
        application = service.submit_application(tenant.id, application_id, current_user.id)
        db.commit()
        return APIResponse(data=ApplicationRead.model_validate(application))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── Loadings ──────────────────────────────────────────────────────────────────

@router.get("/{application_id}/loadings", response_model=APIResponse)
def list_loadings(
    application_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(LOADING_READ)),
):
    service = ApplicationService(db, AuditService(db))
    if not service.get_by_id(tenant.id, application_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    loadings = service.list_loadings(tenant.id, application_id)
    return APIResponse(data=[LoadingRead.model_validate(l) for l in loadings])


@router.post("/{application_id}/loadings", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def add_loading(
    application_id: str,
    body: LoadingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(LOADING_APPLY)),
):
    service = ApplicationService(db, AuditService(db))
    try:
        loading = service.add_loading(tenant.id, application_id, body, current_user.id)
        db.commit()
        return APIResponse(data=LoadingRead.model_validate(loading))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{application_id}/loadings/{loading_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_loading(
    application_id: str,
    loading_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(LOADING_APPLY)),
):
    service = ApplicationService(db, AuditService(db))
    success = service.remove_loading(tenant.id, application_id, loading_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loading not found")
    db.commit()


# ── Remarks ───────────────────────────────────────────────────────────────────

@router.get("/{application_id}/remarks", response_model=APIResponse)
def get_remarks(
    application_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(APPLICATION_READ)),
):
    service = ApplicationService(db, AuditService(db))
    try:
        remarks = service.get_remarks(tenant.id, application_id)
        return APIResponse(data=remarks)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{application_id}/remarks", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def add_remark(
    application_id: str,
    body: RemarkCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(APPLICATION_READ)),
):
    service = ApplicationService(db, AuditService(db))
    try:
        remark = service.add_remark(
            tenant_id=tenant.id,
            application_id=application_id,
            text=body.text,
            author_id=current_user.id,
            author_name=f"{current_user.first_name} {current_user.last_name}".strip(),
            author_role=current_user.user_type if isinstance(current_user.user_type, str) else current_user.user_type.value,
        )
        db.commit()
        return APIResponse(data=remark)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── Premium recalculation ─────────────────────────────────────────────────────

@router.post("/{application_id}/recalculate", response_model=APIResponse)
def recalculate_premium(
    application_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(APPLICATION_UPDATE)),
):
    service = ApplicationService(db, AuditService(db))
    try:
        application = service.recalculate_premium(tenant.id, application_id, current_user.id)
        db.commit()
        return APIResponse(data=ApplicationRead.model_validate(application))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── Items ─────────────────────────────────────────────────────────────────────

@router.get("/{application_id}/items", response_model=APIResponse)
def list_application_items(
    application_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(APPLICATION_READ)),
):
    service = ApplicationService(db, AuditService(db))
    application = service.get_by_id(tenant.id, application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    items = service.get_items(tenant.id, application_id)
    return APIResponse(data=[ApplicationItemRead.model_validate(i) for i in items])


@router.post("/{application_id}/items", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def add_application_item(
    application_id: str,
    body: ApplicationItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(APPLICATION_UPDATE)),
):
    audit_service = AuditService(db)
    service = ApplicationService(db, audit_service)
    try:
        item = service.add_item(tenant.id, application_id, body, current_user.id)
        db.commit()
        return APIResponse(data=ApplicationItemRead.model_validate(item))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{application_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_application_item(
    application_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(APPLICATION_UPDATE)),
):
    audit_service = AuditService(db)
    service = ApplicationService(db, audit_service)
    try:
        success = service.remove_item(tenant.id, item_id, current_user.id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── Approve / Reject / Issue ──────────────────────────────────────────────────

@router.post("/{application_id}/approve", response_model=APIResponse)
def approve_application(
    application_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(APPLICATION_APPROVE)),
):
    audit_service = AuditService(db)
    service = ApplicationService(db, audit_service)
    try:
        application = service.approve_application(tenant.id, application_id, current_user.id)
        db.commit()
        return APIResponse(data=ApplicationRead.model_validate(application))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{application_id}/reject", response_model=APIResponse)
def reject_application(
    application_id: str,
    reason: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(APPLICATION_REJECT)),
):
    audit_service = AuditService(db)
    service = ApplicationService(db, audit_service)
    try:
        application = service.reject_application(tenant.id, application_id, reason, current_user.id)
        db.commit()
        return APIResponse(data=ApplicationRead.model_validate(application))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{application_id}/issue", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def issue_policy(
    application_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(POLICY_ISSUE)),
):
    audit_service = AuditService(db)
    service = PolicyService(db, audit_service)
    try:
        policy = service.issue_policy(tenant.id, application_id, current_user.id)
        db.commit()
        return APIResponse(data=PolicyRead.model_validate(policy))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
