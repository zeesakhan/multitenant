from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, get_current_user, require_permissions, get_pagination
from app.schemas.base import APIResponse, PaginatedResponse, PaginationParams
from app.schemas.policy import PolicyRead, PolicyListResponse
from app.schemas.document import DocumentListResponse
from app.models.tenant import Tenant
from app.services.policy_service import PolicyService
from app.services.document_service import DocumentService
from app.services.audit_service import AuditService
from app.constants.permissions import POLICY_READ, POLICY_READ_ALL, POLICY_RENEW, DOCUMENT_CREATE, DOCUMENT_READ, DOCUMENT_DOWNLOAD

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.get("", response_model=PaginatedResponse)
def list_policies(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    tenant: Tenant = Depends(require_permissions(POLICY_READ)),
):
    """List all policies for the current tenant."""
    service = PolicyService(db, AuditService(db))
    skip = (pagination.page - 1) * pagination.per_page
    policies, total = service.list_policies(tenant.id, skip=skip, limit=pagination.per_page)

    return PaginatedResponse(
        data=[PolicyListResponse.model_validate(p) for p in policies],
        pagination={"page": pagination.page, "per_page": pagination.per_page, "total": total},
    )


@router.get("/{policy_id}", response_model=APIResponse)
def get_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(POLICY_READ)),
):
    """Get policy details."""
    service = PolicyService(db, AuditService(db))
    policy = service.get_by_id(tenant.id, policy_id)

    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    return APIResponse(data=PolicyRead.model_validate(policy))


@router.post("/{policy_id}/renew", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
def renew_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(POLICY_RENEW)),
):
    """Renew an expiring or expired policy for another year."""
    service = PolicyService(db, AuditService(db))
    try:
        new_policy = service.renew(tenant.id, policy_id, current_user.id)
        db.commit()
        return APIResponse(data=PolicyRead.model_validate(new_policy))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{policy_id}/generate-document", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
def generate_document(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(DOCUMENT_CREATE)),
):
    """Generate a policy document (HTML certificate)."""
    policy_service = PolicyService(db, AuditService(db))
    policy = policy_service.get_by_id(tenant.id, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    doc_service = DocumentService(db, AuditService(db))
    doc = doc_service.generate_policy_document(tenant.id, policy, current_user.id)
    db.commit()
    return APIResponse(data={"id": doc.id, "file_name": doc.file_name, "created_at": doc.created_at.isoformat()})


@router.get("/{policy_id}/documents", response_model=APIResponse)
def list_policy_documents(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(DOCUMENT_READ)),
):
    """List documents generated for this policy."""
    doc_service = DocumentService(db, AuditService(db))
    docs = doc_service.list_by_entity(tenant.id, "policy", policy_id)
    return APIResponse(data=[{"id": d.id, "file_name": d.file_name, "mime_type": d.mime_type, "created_at": d.created_at.isoformat()} for d in docs])


@router.get("/{policy_id}/documents/{document_id}/download")
def download_policy_document(
    policy_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(DOCUMENT_DOWNLOAD)),
):
    """Download a policy document."""
    doc_service = DocumentService(db, AuditService(db))
    doc = doc_service.get_document(tenant.id, document_id)
    if not doc or doc.entity_id != policy_id:
        raise HTTPException(status_code=404, detail="Document not found")
    content = doc_service.get_file_content(tenant.id, document_id)
    return Response(content=content, media_type=doc.mime_type,
                    headers={"Content-Disposition": f'attachment; filename="{doc.file_name}"'})
