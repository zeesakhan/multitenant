from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.document import DocumentTemplate, DocumentUpload
from app.schemas.document import DocumentTemplateCreate, DocumentUploadCreate
from app.services.audit_service import AuditService
from app.constants.enums import DocumentType
import os
import uuid
import base64


class DocumentService:
    def __init__(self, db: Session, audit_service: AuditService, storage_path: str = "/storage"):
        self.db = db
        self.audit = audit_service
        self.storage_path = storage_path

    def create_template(
        self,
        tenant_id: str,
        data: DocumentTemplateCreate,
        user_id: str,
    ) -> DocumentTemplate:
        """Create a new document template."""
        template = DocumentTemplate(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            code=data.code,
            template_type=data.template_type,
            description=data.description,
            required_fields=data.required_fields,
            mime_types=data.mime_types,
            max_size_kb=data.max_size_kb,
            is_required=data.is_required,
        )

        self.db.add(template)
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="create",
            entity_type="document_template",
            entity_id=template.id,
            user_id=user_id,
        )

        return template

    def get_template(self, tenant_id: str, template_id: str) -> DocumentTemplate:
        return self.db.query(DocumentTemplate).filter(
            and_(DocumentTemplate.tenant_id == tenant_id, DocumentTemplate.id == template_id)
        ).first()

    def get_template_by_code(self, tenant_id: str, code: str) -> DocumentTemplate:
        return self.db.query(DocumentTemplate).filter(
            and_(DocumentTemplate.tenant_id == tenant_id, DocumentTemplate.code == code)
        ).first()

    def list_templates(
        self,
        tenant_id: str,
        template_type: str = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[DocumentTemplate], int]:
        query = self.db.query(DocumentTemplate).filter(DocumentTemplate.tenant_id == tenant_id)

        if template_type:
            query = query.filter(DocumentTemplate.template_type == template_type)

        total = query.count()
        templates = query.order_by(DocumentTemplate.created_at.desc()).offset(skip).limit(limit).all()
        return templates, total

    def upload_document(
        self,
        tenant_id: str,
        file_name: str,
        file_content: bytes,
        document_type: DocumentType,
        entity_type: str,
        entity_id: str,
        user_id: str,
    ) -> DocumentUpload:
        """Upload a document."""
        file_size = len(file_content)

        # Determine mime type from filename
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_name)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Store file
        file_path = self._store_file(tenant_id, entity_type, entity_id, document_type, file_name, file_content)

        # Create document record
        document = DocumentUpload(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            document_type=document_type,
            entity_type=entity_type,
            entity_id=entity_id,
            uploaded_by=user_id,
            validation_status="pending",
        )

        self.db.add(document)
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="create",
            entity_type="document_upload",
            entity_id=document.id,
            user_id=user_id,
        )

        return document

    def _store_file(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        document_type: DocumentType,
        file_name: str,
        file_content: bytes,
    ) -> str:
        """Store file — uses disk when storage_path is writable, inline base64 otherwise."""
        try:
            dir_path = os.path.join(
                self.storage_path,
                tenant_id,
                entity_type,
                entity_id,
                document_type.value if hasattr(document_type, 'value') else str(document_type),
            )
            os.makedirs(dir_path, exist_ok=True)
            name, ext = os.path.splitext(file_name)
            unique_name = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
            file_path = os.path.join(dir_path, unique_name)
            with open(file_path, "wb") as f:
                f.write(file_content)
            return file_path
        except OSError:
            return "inline:base64:" + base64.b64encode(file_content).decode("ascii")

    def get_document(self, tenant_id: str, document_id: str) -> DocumentUpload:
        return self.db.query(DocumentUpload).filter(
            and_(DocumentUpload.tenant_id == tenant_id, DocumentUpload.id == document_id)
        ).first()

    def list_by_entity(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
    ) -> list[DocumentUpload]:
        return self.db.query(DocumentUpload).filter(
            and_(
                DocumentUpload.tenant_id == tenant_id,
                DocumentUpload.entity_type == entity_type,
                DocumentUpload.entity_id == entity_id,
            )
        ).order_by(DocumentUpload.created_at.desc()).all()

    def list_by_type(
        self,
        tenant_id: str,
        document_type: DocumentType,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[DocumentUpload], int]:
        query = self.db.query(DocumentUpload).filter(
            and_(
                DocumentUpload.tenant_id == tenant_id,
                DocumentUpload.document_type == document_type,
            )
        )

        total = query.count()
        documents = query.order_by(DocumentUpload.created_at.desc()).offset(skip).limit(limit).all()
        return documents, total

    def validate_document(
        self,
        tenant_id: str,
        document_id: str,
        user_id: str,
    ) -> DocumentUpload:
        """Validate a document (placeholder for actual validation logic)."""
        document = self.get_document(tenant_id, document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Placeholder validation - in real implementation would do OCR, content checks, etc.
        document.validation_status = "valid"
        document.validation_errors = None

        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="update",
            entity_type="document_upload",
            entity_id=document.id,
            user_id=user_id,
            new_values={"validation_status": "valid"},
        )

        return document

    def delete_document(
        self,
        tenant_id: str,
        document_id: str,
        user_id: str,
    ) -> bool:
        """Delete a document."""
        document = self.get_document(tenant_id, document_id)
        if not document:
            return False

        # Delete file from storage
        if os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except OSError:
                # Log but don't fail if file doesn't exist
                pass

        # Delete record
        self.db.delete(document)
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="delete",
            entity_type="document_upload",
            entity_id=document_id,
            user_id=user_id,
        )

        return True

    def generate_policy_document(self, tenant_id: str, policy, user_id: str) -> DocumentUpload:
        """Generate an HTML policy document and store inline (dev mode)."""
        html = self._render_policy_html(policy)
        content = html.encode("utf-8")
        file_name = f"policy_{policy.policy_number}.html"

        # Store inline as base64 so dev mode works without a filesystem
        inline_path = "inline:base64:" + base64.b64encode(content).decode("ascii")

        document = DocumentUpload(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            file_name=file_name,
            file_path=inline_path,
            file_size=len(content),
            mime_type="text/html",
            document_type=DocumentType.POLICY_DOCUMENT,
            entity_type="policy",
            entity_id=policy.id,
            uploaded_by=user_id,
            validation_status="valid",
        )
        self.db.add(document)
        self.db.flush()
        self.audit.log(tenant_id=tenant_id, action="generate", entity_type="document_upload",
                       entity_id=document.id, user_id=user_id,
                       new_values={"policy_id": policy.id, "file_name": file_name})
        return document

    def _render_policy_html(self, policy) -> str:
        eff = policy.effective_date.strftime("%B %d, %Y") if hasattr(policy.effective_date, "strftime") else str(policy.effective_date)
        exp = policy.expiry_date.strftime("%B %d, %Y") if hasattr(policy.expiry_date, "strftime") else str(policy.expiry_date)
        issued = policy.issued_at.strftime("%B %d, %Y") if policy.issued_at and hasattr(policy.issued_at, "strftime") else "—"
        return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Policy {policy.policy_number}</title>
<style>
  body{{font-family:Georgia,serif;max-width:800px;margin:40px auto;padding:40px;color:#1a1a2e;}}
  .header{{text-align:center;border-bottom:3px double #2d5a8e;padding-bottom:20px;margin-bottom:30px;}}
  .badge{{display:inline-block;background:#2d5a8e;color:white;padding:6px 20px;border-radius:4px;font-size:13px;letter-spacing:1px;}}
  .policy-num{{font-size:28px;font-weight:bold;font-family:monospace;margin:10px 0;color:#2d5a8e;}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:20px 0;}}
  .field{{background:#f8f9fa;padding:12px 16px;border-left:3px solid #2d5a8e;}}
  .label{{font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#666;}}
  .value{{font-size:16px;font-weight:bold;margin-top:4px;}}
  .footer{{margin-top:40px;text-align:center;font-size:12px;color:#999;border-top:1px solid #eee;padding-top:20px;}}
  .seal{{font-size:48px;margin:10px;}}
</style>
</head>
<body>
<div class="header">
  <div class="badge">INSURANCE POLICY</div>
  <div class="policy-num">{policy.policy_number}</div>
  <div>Certificate of Insurance</div>
</div>
<div class="grid">
  <div class="field"><div class="label">Policyholder</div><div class="value">{policy.customer_name}</div></div>
  <div class="field"><div class="label">Email</div><div class="value">{policy.customer_email}</div></div>
  <div class="field"><div class="label">Effective Date</div><div class="value">{eff}</div></div>
  <div class="field"><div class="label">Expiry Date</div><div class="value">{exp}</div></div>
  <div class="field"><div class="label">Total Premium</div><div class="value">${float(policy.total_premium):,.2f}/month</div></div>
  <div class="field"><div class="label">Covered Members</div><div class="value">{policy.member_count}</div></div>
  <div class="field"><div class="label">Status</div><div class="value">{policy.status.upper()}</div></div>
  <div class="field"><div class="label">Issue Date</div><div class="value">{issued}</div></div>
</div>
<div class="footer">
  <div class="seal">🛡️</div>
  <p>This document serves as proof of insurance coverage.</p>
  <p>Policy Number: {policy.policy_number} &nbsp;|&nbsp; Generated: {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d')}</p>
</div>
</body></html>"""

    def get_file_content(self, tenant_id: str, document_id: str) -> bytes:
        """Get file content — supports inline base64 (dev) and disk storage."""
        document = self.get_document(tenant_id, document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        if document.file_path.startswith("inline:base64:"):
            return base64.b64decode(document.file_path[len("inline:base64:"):])

        if not os.path.exists(document.file_path):
            raise ValueError(f"File not found: {document.file_path}")

        with open(document.file_path, "rb") as f:
            return f.read()
