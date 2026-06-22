"""AML (Anti-Money Laundering) API endpoints.

Tipping-off protection: none of these endpoints are exposed to customers.
All require AML_READ minimum. The application status shown to policyholders
must use a generic label — never "AML Hold".
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal

from app.api.v1.dependencies import get_db, get_current_user, require_permissions
from app.schemas.base import APIResponse, PaginatedResponse
from app.models.tenant import Tenant
from app.models.compliance import AmlRecord, StrRecord
from app.services.aml_service import get_aml_service
from app.services.audit_service import AuditService
from app.constants.permissions import AML_READ, AML_CLEAR, AML_OVERRIDE, STR_CREATE, STR_APPROVE, STR_FILE
from app.constants.enums import StrStatus

router = APIRouter(prefix="/aml", tags=["AML & Compliance"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class AmlClearRequest(BaseModel):
    notes: str = Field(..., min_length=10, max_length=2000)


class AmlAlertRead(BaseModel):
    application_id: str
    application_number: str
    customer_name: str
    aml_status: str
    aml_risk_score: Optional[Decimal] = None
    status: str
    created_at: str


class StrCreateRequest(BaseModel):
    application_id: Optional[str] = None
    nature_of_suspicion: str = Field(..., min_length=20, max_length=2000)
    subject_details: dict = Field(default_factory=dict)
    transaction_details: dict = Field(default_factory=dict)


class StrApproveRequest(BaseModel):
    notes: str = Field(..., min_length=10, max_length=1000)


# ── AML Alerts ────────────────────────────────────────────────────────────────

@router.get("/alerts", response_model=APIResponse)
def list_aml_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(AML_READ)),
):
    """List all applications currently flagged or on AML Hold."""
    aml_svc = get_aml_service(db, AuditService(db))
    applications = aml_svc.list_alerts(tenant.id)

    data = [
        {
            "application_id": a.id,
            "application_number": a.application_number,
            "customer_name": a.customer_name,
            "aml_status": a.aml_status,
            "aml_risk_score": str(a.aml_risk_score) if a.aml_risk_score else None,
            "status": a.status if isinstance(a.status, str) else a.status.value,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in applications
    ]
    return APIResponse(data=data)


@router.get("/records/{application_id}", response_model=APIResponse)
def list_aml_records(
    application_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(AML_READ)),
):
    """Get all AML check records for an application."""
    records = db.query(AmlRecord).filter(
        AmlRecord.tenant_id == tenant.id,
        AmlRecord.application_id == application_id,
    ).order_by(AmlRecord.checked_at.desc()).all()

    data = [
        {
            "id": r.id,
            "check_type": r.check_type,
            "status": r.status,
            "risk_score": str(r.risk_score) if r.risk_score else None,
            "checked_at": r.checked_at.isoformat() if r.checked_at else None,
            "cleared_at": r.cleared_at.isoformat() if r.cleared_at else None,
            "clearance_notes": r.clearance_notes,
        }
        for r in records
    ]
    return APIResponse(data=data)


@router.post("/{application_id}/clear", response_model=APIResponse)
def clear_aml_hold(
    application_id: str,
    body: AmlClearRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(AML_CLEAR)),
):
    """Clear an AML hold — Compliance Officer only."""
    aml_svc = get_aml_service(db, AuditService(db))
    try:
        application = aml_svc.clear_aml_hold(tenant.id, application_id, current_user.id, body.notes)
        db.commit()
        return APIResponse(data={
            "application_id": application.id,
            "aml_status": application.aml_status,
            "status": application.status if isinstance(application.status, str) else application.status.value,
        })
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{application_id}/hold", response_model=APIResponse)
def place_aml_hold(
    application_id: str,
    body: AmlClearRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(AML_OVERRIDE)),
):
    """Manually place an AML hold on an application."""
    aml_svc = get_aml_service(db, AuditService(db))
    try:
        aml_svc.place_aml_hold(tenant.id, application_id, body.notes, current_user.id)
        db.commit()
        return APIResponse(data={"application_id": application_id, "aml_status": "hold"})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── STR (Suspicious Transaction Reports) ──────────────────────────────────────

@router.get("/str", response_model=APIResponse)
def list_str_records(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(STR_CREATE)),
):
    """List all STR records. Compliance Officer + Admin only."""
    records = db.query(StrRecord).filter(
        StrRecord.tenant_id == tenant.id,
    ).order_by(StrRecord.created_at.desc()).all()

    data = [
        {
            "id": r.id,
            "str_reference": r.str_reference,
            "application_id": r.application_id,
            "status": r.status,
            "nature_of_suspicion": r.nature_of_suspicion[:100] + "..." if r.nature_of_suspicion and len(r.nature_of_suspicion) > 100 else r.nature_of_suspicion,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "approved_at": r.approved_at.isoformat() if r.approved_at else None,
            "filed_at": r.filed_at.isoformat() if r.filed_at else None,
        }
        for r in records
    ]
    return APIResponse(data=data)


@router.post("/str", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def create_str(
    body: StrCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(STR_CREATE)),
):
    """Create a new Suspicious Transaction Report (draft)."""
    import uuid
    from datetime import datetime, timezone

    str_ref = f"STR-{uuid.uuid4().hex[:8].upper()}"
    record = StrRecord(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        str_reference=str_ref,
        application_id=body.application_id,
        created_by=current_user.id,
        status=StrStatus.DRAFT.value,
        nature_of_suspicion=body.nature_of_suspicion,
        subject_details=body.subject_details,
        transaction_details=body.transaction_details,
        audit_trail=[{
            "action": "created",
            "by": current_user.id,
            "at": datetime.now(timezone.utc).isoformat(),
        }],
    )
    db.add(record)

    AuditService(db).log(
        tenant_id=tenant.id,
        action="create",
        entity_type="str_record",
        entity_id=record.id,
        user_id=current_user.id,
        new_values={"str_reference": str_ref, "application_id": body.application_id},
    )

    db.commit()
    return APIResponse(data={"id": record.id, "str_reference": str_ref, "status": record.status})


@router.post("/str/{str_id}/approve", response_model=APIResponse)
def approve_str(
    str_id: str,
    body: StrApproveRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(STR_APPROVE)),
):
    """Approve an STR (dual authorisation — Senior Management/Admin)."""
    from datetime import datetime, timezone

    record = db.query(StrRecord).filter(
        StrRecord.tenant_id == tenant.id,
        StrRecord.id == str_id,
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="STR not found")
    if record.status != StrStatus.DRAFT.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"STR is in {record.status} status, not draft")

    now = datetime.now(timezone.utc)
    record.status = StrStatus.APPROVED.value
    record.approver_id = current_user.id
    record.approved_at = now
    trail = list(record.audit_trail or [])
    trail.append({"action": "approved", "by": current_user.id, "at": now.isoformat(), "notes": body.notes})
    record.audit_trail = trail

    AuditService(db).log(
        tenant_id=tenant.id,
        action="approve",
        entity_type="str_record",
        entity_id=str_id,
        user_id=current_user.id,
    )

    db.commit()
    return APIResponse(data={"id": record.id, "status": record.status})


@router.post("/str/{str_id}/file", response_model=APIResponse)
def file_str(
    str_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(STR_FILE)),
):
    """Mark an approved STR as filed with the FIU."""
    from datetime import datetime, timezone

    record = db.query(StrRecord).filter(
        StrRecord.tenant_id == tenant.id,
        StrRecord.id == str_id,
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="STR not found")
    if record.status != StrStatus.APPROVED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="STR must be approved before filing")

    now = datetime.now(timezone.utc)
    record.status = StrStatus.FILED.value
    record.filed_at = now
    trail = list(record.audit_trail or [])
    trail.append({"action": "filed", "by": current_user.id, "at": now.isoformat()})
    record.audit_trail = trail

    AuditService(db).log(
        tenant_id=tenant.id,
        action="file",
        entity_type="str_record",
        entity_id=str_id,
        user_id=current_user.id,
    )

    db.commit()
    return APIResponse(data={"id": record.id, "status": record.status, "filed_at": now.isoformat()})
