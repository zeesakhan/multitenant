from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, require_super_admin, get_pagination
from app.services.tenant_service import TenantService
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.schemas.base import PaginationParams
from app.utils.formatters import api_response, paginated_response

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post("", response_model=dict)
def create_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
    _=Depends(require_super_admin),
):
    svc = TenantService(db)
    tenant = svc.create(payload)
    return api_response(data={"id": tenant.id, "code": tenant.code, "name": tenant.name}, message="Tenant created successfully.")


@router.get("", response_model=dict)
def list_tenants(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
    _=Depends(require_super_admin),
):
    svc = TenantService(db)
    tenants, total = svc.list_all(skip=pagination.offset, limit=pagination.per_page)
    data = [{"id": t.id, "code": t.code, "name": t.name, "status": t.status} for t in tenants]
    return paginated_response(data, total, pagination.page, pagination.per_page)


@router.get("/{tenant_id}", response_model=dict)
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_super_admin),
):
    svc = TenantService(db)
    tenant = svc.get_by_id(tenant_id)
    return api_response(data={"id": tenant.id, "code": tenant.code, "name": tenant.name, "status": tenant.status, "config": tenant.config})


@router.put("/{tenant_id}", response_model=dict)
def update_tenant(
    tenant_id: str,
    payload: TenantUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_super_admin),
):
    svc = TenantService(db)
    tenant = svc.update(tenant_id, payload)
    return api_response(data={"id": tenant.id, "code": tenant.code, "name": tenant.name, "status": tenant.status}, message="Tenant updated.")
