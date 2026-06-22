"""Government Verification Checks API.

Endpoints for triggering, listing, and overriding ICP/DHA/Sanctions checks.
Requires GOVT_CHECK_READ minimum.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.api.v1.dependencies import get_db, get_current_user, require_permissions
from app.schemas.base import APIResponse, PaginatedResponse
from app.models.tenant import Tenant
from app.models.compliance import GovtVerificationRecord
from app.models.member import Member
from app.models.application import Application
from app.services.govt_verification_service import get_govt_service
from app.services.audit_service import AuditService
from app.constants.permissions import GOVT_CHECK_READ, GOVT_CHECK_OVERRIDE, GOVT_CHECK_RETRY

router = APIRouter(prefix="/govt-checks", tags=["Government Checks"])


class IcpVerifyRequest(BaseModel):
    member_id: str
    emirates_id: str = Field(..., pattern=r"^784-\d{4}-\d{7}-\d$")


class SanctionsVerifyRequest(BaseModel):
    member_id: str
    full_name: str = Field(..., min_length=2)
    date_of_birth: date
    nationality: str = Field(..., min_length=2, max_length=3)


class OverrideRequest(BaseModel):
    justification: str = Field(..., min_length=20, max_length=2000)


# ── Trigger checks ────────────────────────────────────────────────────────────

@router.post("/applications/{application_id}/verify-icp", response_model=APIResponse)
def trigger_icp_check(
    application_id: str,
    body: IcpVerifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(GOVT_CHECK_READ)),
):
    """Trigger ICP Emirates ID check for a member."""
    member = db.query(Member).filter(
        Member.tenant_id == tenant.id,
        Member.id == body.member_id,
        Member.application_id == application_id,
    ).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    svc = get_govt_service(db, AuditService(db))
    result = svc.verify_icp(
        tenant_id=tenant.id,
        application_id=application_id,
        member_id=body.member_id,
        emirates_id=body.emirates_id,
        full_name=f"{member.first_name} {member.last_name}",
        dob=member.date_of_birth,
        user_id=current_user.id,
    )
    db.commit()

    return APIResponse(data={
        "record_id": result.record_id,
        "status": result.status,
        "matched": result.matched,
        "passed": result.passed,
    })


@router.post("/applications/{application_id}/verify-sanctions", response_model=APIResponse)
def trigger_sanctions_check(
    application_id: str,
    body: SanctionsVerifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(GOVT_CHECK_READ)),
):
    """Trigger all sanctions list checks (OFAC, UN, UAE Cabinet 74)."""
    svc = get_govt_service(db, AuditService(db))
    results = svc.run_all_sanctions(
        tenant_id=tenant.id,
        application_id=application_id,
        member_id=body.member_id,
        full_name=body.full_name,
        dob=body.date_of_birth,
        nationality=body.nationality,
        user_id=current_user.id,
    )
    db.commit()

    return APIResponse(data=[
        {"record_id": r.record_id, "status": r.status, "matched": r.matched, "passed": r.passed}
        for r in results
    ])


# ── List / Overview ───────────────────────────────────────────────────────────

@router.get("", response_model=APIResponse)
def list_govt_checks(
    status_filter: Optional[str] = None,
    check_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(GOVT_CHECK_READ)),
):
    """List all pending/failed government verification records."""
    svc = get_govt_service(db, AuditService(db))

    if status_filter or check_type:
        query = db.query(GovtVerificationRecord).filter(
            GovtVerificationRecord.tenant_id == tenant.id,
        )
        if status_filter:
            query = query.filter(GovtVerificationRecord.status == status_filter)
        if check_type:
            query = query.filter(GovtVerificationRecord.check_type == check_type)
        records = query.order_by(GovtVerificationRecord.created_at.desc()).limit(200).all()
    else:
        records = svc.list_pending(tenant.id)

    data = [
        {
            "id": r.id,
            "application_id": r.application_id,
            "member_id": r.member_id,
            "check_type": r.check_type,
            "status": r.status,
            "triggered_at": r.triggered_at.isoformat() if r.triggered_at else None,
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
            "overridden_by": r.overridden_by,
            "override_justification": r.override_justification,
        }
        for r in records
    ]
    return APIResponse(data=data)


@router.get("/applications/{application_id}", response_model=APIResponse)
def list_application_checks(
    application_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(GOVT_CHECK_READ)),
):
    """Get all govt verification records for a specific application."""
    records = db.query(GovtVerificationRecord).filter(
        GovtVerificationRecord.tenant_id == tenant.id,
        GovtVerificationRecord.application_id == application_id,
    ).order_by(GovtVerificationRecord.triggered_at.desc()).all()

    data = [
        {
            "id": r.id,
            "member_id": r.member_id,
            "check_type": r.check_type,
            "status": r.status,
            "response_payload": r.response_payload,
            "triggered_at": r.triggered_at.isoformat() if r.triggered_at else None,
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        }
        for r in records
    ]
    return APIResponse(data=data)


# ── Override ──────────────────────────────────────────────────────────────────

@router.post("/{record_id}/override", response_model=APIResponse)
def override_check(
    record_id: str,
    body: OverrideRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(GOVT_CHECK_OVERRIDE)),
):
    """Manually override a failed or pending verification (Compliance Officer only)."""
    svc = get_govt_service(db, AuditService(db))
    try:
        record = svc.override_check(tenant.id, record_id, current_user.id, body.justification)
        db.commit()
        return APIResponse(data={
            "id": record.id,
            "status": record.status,
            "overridden_by": record.overridden_by,
        })
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/bulk-retry", response_model=APIResponse)
def bulk_retry(
    record_ids: list[str],
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(GOVT_CHECK_RETRY)),
):
    """Re-queue pending/failed checks for retry. Returns count of records updated."""
    from app.constants.enums import GovtVerificationStatus

    records = db.query(GovtVerificationRecord).filter(
        GovtVerificationRecord.tenant_id == tenant.id,
        GovtVerificationRecord.id.in_(record_ids),
        GovtVerificationRecord.status.in_([
            GovtVerificationStatus.PENDING.value,
            GovtVerificationStatus.FAILED.value,
        ]),
    ).all()

    # In mock mode just reset to verified; in real mode would re-trigger
    for record in records:
        record.status = GovtVerificationStatus.PENDING.value

    db.commit()
    return APIResponse(data={"retried": len(records)})
