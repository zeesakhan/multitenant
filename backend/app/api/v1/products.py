from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, get_current_user, require_permissions, get_pagination
from app.schemas.base import APIResponse, PaginatedResponse, PaginationParams
from app.schemas.product import ProductCreate, ProductUpdate, ProductRead, PlanCreate, PlanUpdate, PlanRead, CoverageCreate, CoverageRead
from app.models.tenant import Tenant
from app.services.product_service import ProductService, PlanService
from app.services.audit_service import AuditService
from app.constants.permissions import PRODUCT_CREATE, PRODUCT_READ, PRODUCT_UPDATE, PRODUCT_DELETE, PLAN_CREATE, PLAN_READ, PLAN_UPDATE

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(PRODUCT_CREATE)),
):
    """Create a new product."""
    audit_service = AuditService(db)
    service = ProductService(db, audit_service)

    product = service.create_product(tenant.id, body, current_user.id)
    db.commit()

    return APIResponse(data=ProductRead.model_validate(product))


@router.get("", response_model=PaginatedResponse)
def list_products(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    tenant: Tenant = Depends(require_permissions(PRODUCT_READ)),
):
    """List all products for the current tenant."""
    service = ProductService(db, AuditService(db))

    skip = (pagination.page - 1) * pagination.per_page
    products, total = service.list_products(tenant.id, skip, pagination.per_page)

    return PaginatedResponse(
        data=[ProductRead.model_validate(p) for p in products],
        pagination={
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": total,
        }
    )


@router.get("/{product_id}", response_model=APIResponse)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(PRODUCT_READ)),
):
    """Get product details."""
    service = ProductService(db, AuditService(db))
    product = service.get_by_id(tenant.id, product_id)

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    return APIResponse(data=ProductRead.model_validate(product))


@router.put("/{product_id}", response_model=APIResponse)
def update_product(
    product_id: str,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(PRODUCT_UPDATE)),
):
    """Update product details."""
    audit_service = AuditService(db)
    service = ProductService(db, audit_service)

    product = service.update_product(tenant.id, product_id, body, current_user.id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    db.commit()
    return APIResponse(data=ProductRead.model_validate(product))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(PRODUCT_DELETE)),
):
    """Delete a product."""
    audit_service = AuditService(db)
    service = ProductService(db, audit_service)

    success = service.delete_product(tenant.id, product_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    db.commit()


@router.post("/{product_id}/plans", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def create_plan(
    product_id: str,
    body: PlanCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(PLAN_CREATE)),
):
    """Create a new plan for a product."""
    product_service = ProductService(db, AuditService(db))
    product = product_service.get_by_id(tenant.id, product_id)

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    plan_service = PlanService(db, AuditService(db))
    plan = plan_service.create_plan(tenant.id, product_id, body, current_user.id)
    db.commit()

    return APIResponse(data=PlanRead.model_validate(plan))


@router.get("/{product_id}/plans", response_model=PaginatedResponse)
def list_plans(
    product_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    tenant: Tenant = Depends(require_permissions(PLAN_READ)),
):
    """List all plans for a product."""
    product_service = ProductService(db, AuditService(db))
    product = product_service.get_by_id(tenant.id, product_id)

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    plan_service = PlanService(db, AuditService(db))
    skip = (pagination.page - 1) * pagination.per_page
    plans, total = plan_service.list_plans(tenant.id, product_id, skip, pagination.per_page)

    return PaginatedResponse(
        data=[PlanRead.model_validate(p) for p in plans],
        pagination={
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": total,
        }
    )


@router.get("/{product_id}/plans/{plan_id}", response_model=APIResponse)
def get_plan(
    product_id: str,
    plan_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(PLAN_READ)),
):
    """Get plan details including coverages."""
    plan_service = PlanService(db, AuditService(db))
    plan = plan_service.get_by_id(tenant.id, plan_id)

    if not plan or plan.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    return APIResponse(data=PlanRead.model_validate(plan))


@router.put("/{product_id}/plans/{plan_id}", response_model=APIResponse)
def update_plan(
    product_id: str,
    plan_id: str,
    body: PlanUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(PLAN_UPDATE)),
):
    """Update plan details."""
    plan_service = PlanService(db, AuditService(db))
    plan = plan_service.get_by_id(tenant.id, plan_id)

    if not plan or plan.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    plan = plan_service.update_plan(tenant.id, plan_id, body, current_user.id)
    db.commit()

    return APIResponse(data=PlanRead.model_validate(plan))


@router.post("/{product_id}/plans/{plan_id}/coverages", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def add_coverage(
    product_id: str,
    plan_id: str,
    body: CoverageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(PLAN_UPDATE)),
):
    """Add coverage to a plan."""
    plan_service = PlanService(db, AuditService(db))
    plan = plan_service.get_by_id(tenant.id, plan_id)

    if not plan or plan.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    coverage = plan_service.add_coverage(tenant.id, plan_id, body, current_user.id)
    db.commit()

    return APIResponse(data=CoverageRead.model_validate(coverage))
