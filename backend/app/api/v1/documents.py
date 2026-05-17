from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, get_current_user, require_permissions, get_pagination
from app.schemas.base import APIResponse, PaginatedResponse, PaginationParams
from app.schemas.document import (
    DocumentTemplateCreate, DocumentTemplateRead, DocumentTemplateListResponse,
    DocumentUploadRead, DocumentListResponse,
)
from app.models.tenant import Tenant
from app.services.document_service import DocumentService
from app.services.audit_service import AuditService
from app.constants.enums import DocumentType
from app.constants.permissions import (
    DOCUMENT_CREATE, DOCUMENT_READ, DOCUMENT_DOWNLOAD, DOCUMENT_TEMPLATE_MANAGE,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/templates", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def create_document_template(
    body: DocumentTemplateCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_TEMPLATE_MANAGE)),
):
    """Create a document template."""
    audit_service = AuditService(db)
    service = DocumentService(db, audit_service)

    template = service.create_template(tenant.id, body, current_user.id)
    db.commit()

    return APIResponse(data=DocumentTemplateRead.model_validate(template))


@router.get("/templates", response_model=PaginatedResponse)
def list_document_templates(
    template_type: str = None,
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_TEMPLATE_MANAGE)),
):
    """List document templates."""
    service = DocumentService(db, AuditService(db))

    skip = (pagination.page - 1) * pagination.per_page
    templates, total = service.list_templates(tenant.id, template_type=template_type, skip=skip, limit=pagination.per_page)

    return PaginatedResponse(
        data=[DocumentTemplateListResponse.model_validate(t) for t in templates],
        pagination={
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": total,
        }
    )


@router.get("/templates/{template_id}", response_model=APIResponse)
def get_document_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_TEMPLATE_MANAGE)),
):
    """Get document template."""
    service = DocumentService(db, AuditService(db))
    template = service.get_template(tenant.id, template_id)

    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    return APIResponse(data=DocumentTemplateRead.model_validate(template))


@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(None),
    entity_type: str = Form(None),
    entity_id: str = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_CREATE)),
):
    """Upload a document."""
    if not document_type or not entity_type or not entity_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required parameters")

    try:
        doc_type = DocumentType[document_type.upper()]
    except KeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid document type: {document_type}")

    audit_service = AuditService(db)
    service = DocumentService(db, audit_service)

    try:
        file_content = await file.read()

        document = service.upload_document(
            tenant.id,
            file.filename,
            file_content,
            doc_type,
            entity_type,
            entity_id,
            current_user.id,
        )
        db.commit()

        return APIResponse(data=DocumentUploadRead.model_validate(document))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=PaginatedResponse)
def list_documents(
    entity_type: str = None,
    entity_id: str = None,
    document_type: str = None,
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_READ)),
):
    """List documents."""
    service = DocumentService(db, AuditService(db))

    if entity_type and entity_id:
        documents = service.list_by_entity(tenant.id, entity_type, entity_id)
        return PaginatedResponse(
            data=[DocumentListResponse.model_validate(d) for d in documents],
            pagination={"page": 1, "per_page": len(documents), "total": len(documents)}
        )

    if document_type:
        try:
            doc_type = DocumentType[document_type.upper()]
        except KeyError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid document type: {document_type}")

        skip = (pagination.page - 1) * pagination.per_page
        documents, total = service.list_by_type(tenant.id, doc_type, skip=skip, limit=pagination.per_page)

        return PaginatedResponse(
            data=[DocumentListResponse.model_validate(d) for d in documents],
            pagination={
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": total,
            }
        )

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide either entity_type/entity_id or document_type")


@router.get("/{document_id}", response_model=APIResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_READ)),
):
    """Get document metadata."""
    service = DocumentService(db, AuditService(db))
    document = service.get_document(tenant.id, document_id)

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return APIResponse(data=DocumentUploadRead.model_validate(document))


@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_DOWNLOAD)),
):
    """Download a document."""
    service = DocumentService(db, AuditService(db))
    document = service.get_document(tenant.id, document_id)

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        file_content = service.get_file_content(tenant.id, document_id)
        return FileResponse(
            content=file_content,
            media_type=document.mime_type,
            filename=document.file_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_CREATE)),
):
    """Delete a document."""
    audit_service = AuditService(db)
    service = DocumentService(db, audit_service)

    success = service.delete_document(tenant.id, document_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    db.commit()


@router.post("/{document_id}/validate", response_model=APIResponse)
def validate_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_CREATE)),
):
    """Trigger document validation."""
    audit_service = AuditService(db)
    service = DocumentService(db, audit_service)

    try:
        document = service.validate_document(tenant.id, document_id, current_user.id)
        db.commit()
        return APIResponse(data=DocumentUploadRead.model_validate(document))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
