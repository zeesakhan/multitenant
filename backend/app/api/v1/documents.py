from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse, Response
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


# ── PDF Generation Endpoints ──────────────────────────────────────────────────

def _pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _get_pdf_deps(db, tenant_id, application_id):
    """Load application, members, plan objects needed for PDF context."""
    from app.models.application import Application
    from app.models.member import Member
    from app.models.product import Plan

    app = db.query(Application).filter(
        Application.tenant_id == tenant_id, Application.id == application_id
    ).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    members = db.query(Member).filter(
        Member.tenant_id == tenant_id, Member.application_id == application_id
    ).all()

    plan = db.query(Plan).filter(Plan.id == app.plan_id).first() if app.plan_id else None
    return app, members, plan


@router.post("/applications/{application_id}/generate-maf")
def generate_maf(
    application_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_CREATE)),
):
    """Generate MAF PDF for an application."""
    from app.services.pdf_service import render_pdf, PdfContextBuilder
    app, members, plan = _get_pdf_deps(db, tenant.id, application_id)
    tenant_config = {"company_name": "Adamjee Insurance"}
    ctx = PdfContextBuilder.maf_context(app, members, plan, tenant_config)
    pdf = render_pdf("maf.html", ctx)
    return _pdf_response(pdf, f"MAF-{app.application_number}.pdf")


@router.post("/applications/{application_id}/generate-kyc")
def generate_kyc(
    application_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_CREATE)),
):
    """Generate KYC PDF for an application."""
    from app.services.pdf_service import render_pdf, PdfContextBuilder
    app, members, plan = _get_pdf_deps(db, tenant.id, application_id)
    principal = members[0] if members else None
    tenant_config = {"company_name": "Adamjee Insurance"}
    ctx = PdfContextBuilder.kyc_context(app, principal, tenant_config)
    pdf = render_pdf("kyc.html", ctx)
    return _pdf_response(pdf, f"KYC-{app.application_number}.pdf")


@router.post("/applications/{application_id}/generate-tob")
def generate_tob(
    application_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_CREATE)),
):
    """Generate Table of Benefits PDF."""
    from app.services.pdf_service import render_pdf, PdfContextBuilder
    from app.models.product import Coverage
    app, members, plan = _get_pdf_deps(db, tenant.id, application_id)
    coverages = db.query(Coverage).filter(Coverage.plan_id == app.plan_id).all() if app.plan_id else []
    tenant_config = {"company_name": "Adamjee Insurance"}
    breakdown = app.premium_breakdown
    ctx = PdfContextBuilder.tob_context(app, plan, coverages, breakdown, tenant_config)
    pdf = render_pdf("tob.html", ctx)
    return _pdf_response(pdf, f"ToB-{app.application_number}.pdf")


@router.post("/policies/{policy_id}/generate-schedule")
def generate_policy_schedule(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_CREATE)),
):
    """Generate Policy Schedule PDF."""
    from app.services.pdf_service import render_pdf, PdfContextBuilder
    from app.models.policy import Policy
    from app.models.application import Application
    from app.models.member import Member
    from app.models.product import Plan
    from app.models.payment import Payment

    policy = db.query(Policy).filter(Policy.tenant_id == tenant.id, Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    app = db.query(Application).filter(Application.id == policy.application_id).first()
    members = db.query(Member).filter(Member.application_id == policy.application_id).all()
    plan = db.query(Plan).filter(Plan.id == app.plan_id).first() if app and app.plan_id else None
    payment = db.query(Payment).filter(Payment.policy_id == policy_id).order_by(Payment.created_at.desc()).first()

    tenant_config = {"company_name": "Adamjee Insurance"}
    breakdown = app.premium_breakdown if app else None
    ctx = PdfContextBuilder.policy_schedule_context(policy, app, members, plan, breakdown, payment, tenant_config)
    pdf = render_pdf("policy_schedule.html", ctx)
    return _pdf_response(pdf, f"PolicySchedule-{policy.policy_number}.pdf")


@router.post("/policies/{policy_id}/generate-credit-note")
def generate_credit_note(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_CREATE)),
):
    """Generate Credit Note PDF."""
    from app.services.pdf_service import render_pdf, PdfContextBuilder
    from app.models.policy import Policy
    from app.models.application import Application
    from app.models.product import Plan

    policy = db.query(Policy).filter(Policy.tenant_id == tenant.id, Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    app = db.query(Application).filter(Application.id == policy.application_id).first()
    plan = db.query(Plan).filter(Plan.id == app.plan_id).first() if app and app.plan_id else None
    tenant_config = {"company_name": "Adamjee Insurance"}
    ctx = PdfContextBuilder.credit_note_context(policy, app, plan, app.premium_breakdown if app else None, 1, tenant_config)
    pdf = render_pdf("credit_note.html", ctx)
    return _pdf_response(pdf, f"CreditNote-{policy.policy_number}.pdf")


@router.post("/policies/{policy_id}/generate-tax-invoice")
def generate_tax_invoice(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_CREATE)),
):
    """Generate Tax Invoice PDF."""
    from app.services.pdf_service import render_pdf, PdfContextBuilder
    from app.models.policy import Policy
    from app.models.application import Application
    from app.models.product import Plan

    policy = db.query(Policy).filter(Policy.tenant_id == tenant.id, Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    app = db.query(Application).filter(Application.id == policy.application_id).first()
    plan = db.query(Plan).filter(Plan.id == app.plan_id).first() if app and app.plan_id else None
    tenant_config = {"company_name": "Adamjee Insurance"}
    ctx = PdfContextBuilder.tax_invoice_context(policy, app, plan, app.premium_breakdown if app else None, 1, tenant_config)
    pdf = render_pdf("tax_invoice.html", ctx)
    return _pdf_response(pdf, f"TaxInvoice-{policy.policy_number}.pdf")


@router.post("/policies/{policy_id}/generate-receipt")
def generate_receipt(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(DOCUMENT_CREATE)),
):
    """Generate Receipt Voucher PDF."""
    from app.services.pdf_service import render_pdf, PdfContextBuilder
    from app.models.policy import Policy
    from app.models.application import Application
    from app.models.product import Plan
    from app.models.payment import Payment

    policy = db.query(Policy).filter(Policy.tenant_id == tenant.id, Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    app = db.query(Application).filter(Application.id == policy.application_id).first()
    plan = db.query(Plan).filter(Plan.id == app.plan_id).first() if app and app.plan_id else None
    payment = db.query(Payment).filter(Payment.policy_id == policy_id).order_by(Payment.created_at.desc()).first()
    tenant_config = {"company_name": "Adamjee Insurance"}
    ctx = PdfContextBuilder.receipt_context(policy, app, plan, app.premium_breakdown if app else None, payment, 1, tenant_config)
    pdf = render_pdf("receipt_voucher.html", ctx)
    return _pdf_response(pdf, f"Receipt-{policy.policy_number}.pdf")
