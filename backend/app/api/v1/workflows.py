from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, get_current_user, require_permissions, get_pagination
from app.schemas.base import APIResponse, PaginatedResponse, PaginationParams
from app.schemas.workflow import (
    WorkflowDefinitionCreate, WorkflowDefinitionUpdate, WorkflowDefinitionRead,
    WorkflowInstanceRead, WorkflowTransitionRequest, WorkflowCreateInstanceRequest,
)
from app.models.tenant import Tenant
from app.services.workflow_service import WorkflowService
from app.services.audit_service import AuditService
from app.constants.permissions import WORKFLOW_READ, WORKFLOW_MANAGE

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("/definitions", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def create_workflow_definition(
    body: WorkflowDefinitionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(WORKFLOW_MANAGE)),
):
    """Create a new workflow definition."""
    audit_service = AuditService(db)
    service = WorkflowService(db, audit_service)

    try:
        definition = service.create_definition(tenant.id, body, current_user.id)
        db.commit()
        return APIResponse(data=WorkflowDefinitionRead.model_validate(definition))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/definitions", response_model=PaginatedResponse)
def list_workflow_definitions(
    workflow_type: str = None,
    is_active: bool = None,
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(WORKFLOW_READ)),
):
    """List all workflow definitions."""
    service = WorkflowService(db, AuditService(db))

    skip = (pagination.page - 1) * pagination.per_page
    definitions, total = service.list_definitions(
        tenant.id, workflow_type=workflow_type, is_active=is_active, skip=skip, limit=pagination.per_page
    )

    return PaginatedResponse(
        data=[WorkflowDefinitionRead.model_validate(d) for d in definitions],
        pagination={
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": total,
        }
    )


@router.get("/definitions/{definition_id}", response_model=APIResponse)
def get_workflow_definition(
    definition_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(WORKFLOW_READ)),
):
    """Get workflow definition details."""
    service = WorkflowService(db, AuditService(db))
    definition = service.get_definition(tenant.id, definition_id)

    if not definition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow definition not found")

    return APIResponse(data=WorkflowDefinitionRead.model_validate(definition))


@router.put("/definitions/{definition_id}", response_model=APIResponse)
def update_workflow_definition(
    definition_id: str,
    body: WorkflowDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(WORKFLOW_MANAGE)),
):
    """Update workflow definition."""
    audit_service = AuditService(db)
    service = WorkflowService(db, audit_service)

    try:
        definition = service.update_definition(tenant.id, definition_id, body, current_user.id)
        if not definition:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow definition not found")
        db.commit()
        return APIResponse(data=WorkflowDefinitionRead.model_validate(definition))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/instances", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def create_workflow_instance(
    body: WorkflowCreateInstanceRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(WORKFLOW_MANAGE)),
):
    """Create a new workflow instance."""
    audit_service = AuditService(db)
    service = WorkflowService(db, audit_service)

    try:
        instance = service.create_instance(
            tenant.id,
            body.workflow_definition_id,
            body.reference_type,
            body.reference_id,
            body.initial_context,
            current_user.id,
        )
        db.commit()
        return APIResponse(data=WorkflowInstanceRead.model_validate(instance))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/instances/{instance_id}", response_model=APIResponse)
def get_workflow_instance(
    instance_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(WORKFLOW_READ)),
):
    """Get workflow instance details."""
    service = WorkflowService(db, AuditService(db))
    instance = service.get_instance(tenant.id, instance_id)

    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow instance not found")

    return APIResponse(data=WorkflowInstanceRead.model_validate(instance))


@router.post("/instances/{instance_id}/transition", response_model=APIResponse)
def transition_workflow(
    instance_id: str,
    body: WorkflowTransitionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(WORKFLOW_MANAGE)),
):
    """Perform workflow state transition."""
    audit_service = AuditService(db)
    service = WorkflowService(db, audit_service)

    try:
        instance = service.transition(tenant.id, instance_id, body.action, body.context, current_user.id)
        db.commit()
        return APIResponse(data=WorkflowInstanceRead.model_validate(instance))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
