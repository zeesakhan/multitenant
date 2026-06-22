import csv
import io
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db, get_current_user, require_permissions
from app.schemas.base import APIResponse
from app.services.report_service import ReportService
from app.constants.permissions import REPORT_READ

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/summary", response_model=APIResponse)
def report_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(REPORT_READ)),
):
    return APIResponse(data=ReportService(db).summary(tenant.id))


@router.get("/applications", response_model=APIResponse)
def report_applications(
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(REPORT_READ)),
):
    return APIResponse(data=ReportService(db).applications_by_month(tenant.id, months))


@router.get("/premium", response_model=APIResponse)
def report_premium(
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(REPORT_READ)),
):
    return APIResponse(data=ReportService(db).premium_by_month(tenant.id, months))


@router.get("/claims", response_model=APIResponse)
def report_claims(
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(REPORT_READ)),
):
    return APIResponse(data=ReportService(db).claims_by_month(tenant.id, months))


def _csv_response(rows: list[dict], filename: str) -> Response:
    if not rows:
        return Response(content="No data available\n", media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _pdf_response_stub(report_name: str, rows: list[dict]) -> Response:
    """Returns a minimal HTML-as-PDF stub until WeasyPrint integration is added per report."""
    from app.services.pdf_service import render_pdf
    context = {
        "report_name": report_name,
        "rows": rows,
        "generation_date": date.today().strftime("%d %b %Y"),
    }
    try:
        html = f"""
        <html><body style='font-family: Arial; padding: 20px;'>
        <h2>{report_name}</h2>
        <p>Generated: {context['generation_date']}</p>
        <table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse; width:100%'>
        <thead><tr>{''.join(f'<th>{k}</th>' for k in (rows[0].keys() if rows else ['No data']))}</tr></thead>
        <tbody>
        {''.join('<tr>' + ''.join(f'<td>{v}</td>' for v in r.values()) + '</tr>' for r in rows[:100])}
        </tbody></table>
        </body></html>
        """
        from weasyprint import HTML
        pdf_bytes = HTML(string=html).write_pdf()
        filename = report_name.lower().replace(" ", "_") + ".pdf"
        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    except Exception:
        return Response(content=html.encode(), media_type="text/html")


@router.get("/policies-issued")
def report_policies_issued(
    format: str = Query("csv", regex="^(csv|pdf)$"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(REPORT_READ)),
):
    from app.models.policy import Policy
    from app.models.application import Application
    q = db.query(Policy).filter(Policy.tenant_id == tenant.id)
    if date_from:
        q = q.filter(Policy.issued_at >= date_from)
    if date_to:
        q = q.filter(Policy.issued_at <= date_to)
    rows = [
        {
            "policy_number": p.policy_number,
            "customer_name": p.customer_name,
            "customer_email": p.customer_email,
            "status": p.status,
            "total_premium": str(p.total_premium),
            "effective_date": str(p.effective_date),
            "expiry_date": str(p.expiry_date),
            "issued_at": str(p.issued_at) if p.issued_at else "",
        }
        for p in q.all()
    ]
    if format == "pdf":
        return _pdf_response_stub("Policy Issued Report", rows)
    return _csv_response(rows, "policies_issued.csv")


@router.get("/commission-statement")
def report_commission_statement(
    format: str = Query("csv", regex="^(csv|pdf)$"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(REPORT_READ)),
):
    from app.models.compliance import CommissionConfig
    q = db.query(CommissionConfig).filter(CommissionConfig.tenant_id == tenant.id)
    rows = [
        {
            "plan_id": str(c.plan_id) if c.plan_id else "",
            "broker_id": str(c.broker_id) if c.broker_id else "",
            "insurer_pct": str(c.insurer_pct),
            "broker_pct": str(c.broker_pct),
            "tpa_pct": str(c.tpa_pct),
            "effective_from": str(c.effective_from) if c.effective_from else "",
        }
        for c in q.all()
    ]
    if format == "pdf":
        return _pdf_response_stub("Commission Statement", rows)
    return _csv_response(rows, "commission_statement.csv")


@router.get("/underwriter")
def report_underwriter(
    format: str = Query("csv", regex="^(csv|pdf)$"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(REPORT_READ)),
):
    from app.models.compliance import PremiumLoading
    from app.models.application import Application
    q = db.query(PremiumLoading, Application).join(
        Application, Application.id == PremiumLoading.application_id
    ).filter(PremiumLoading.tenant_id == tenant.id)
    rows = [
        {
            "application_number": app.application_number,
            "customer_name": app.customer_name,
            "loading_type": str(l.loading_type.value if hasattr(l.loading_type, 'value') else l.loading_type),
            "amount": str(l.amount) if l.amount else "",
            "percentage": str(l.percentage) if l.percentage else "",
            "applied_by": str(l.applied_by) if l.applied_by else "",
            "notes": l.notes or "",
        }
        for l, app in q.all()
    ]
    if format == "pdf":
        return _pdf_response_stub("Underwriter Report", rows)
    return _csv_response(rows, "underwriter_report.csv")


@router.get("/aml-screening")
def report_aml_screening(
    format: str = Query("csv", regex="^(csv|pdf)$"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(REPORT_READ)),
):
    from app.models.compliance import AmlRecord
    q = db.query(AmlRecord).filter(AmlRecord.tenant_id == tenant.id)
    if date_from:
        q = q.filter(AmlRecord.checked_at >= date_from)
    if date_to:
        q = q.filter(AmlRecord.checked_at <= date_to)
    rows = [
        {
            "application_id": str(r.application_id),
            "check_type": str(r.check_type.value if hasattr(r.check_type, 'value') else r.check_type),
            "status": str(r.status.value if hasattr(r.status, 'value') else r.status),
            "risk_score": str(r.risk_score) if r.risk_score else "",
            "checked_at": str(r.checked_at) if r.checked_at else "",
            "clearance_notes": r.clearance_notes or "",
        }
        for r in q.all()
    ]
    if format == "pdf":
        return _pdf_response_stub("AML Screening Report", rows)
    return _csv_response(rows, "aml_screening.csv")


@router.get("/govt-verification")
def report_govt_verification(
    format: str = Query("csv", regex="^(csv|pdf)$"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(REPORT_READ)),
):
    from app.models.compliance import GovtVerificationRecord
    q = db.query(GovtVerificationRecord).filter(GovtVerificationRecord.tenant_id == tenant.id)
    if date_from:
        q = q.filter(GovtVerificationRecord.triggered_at >= date_from)
    if date_to:
        q = q.filter(GovtVerificationRecord.triggered_at <= date_to)
    rows = [
        {
            "application_id": str(r.application_id),
            "check_type": str(r.check_type.value if hasattr(r.check_type, 'value') else r.check_type),
            "status": str(r.status.value if hasattr(r.status, 'value') else r.status),
            "triggered_at": str(r.triggered_at) if r.triggered_at else "",
            "resolved_at": str(r.resolved_at) if r.resolved_at else "",
            "override_justification": r.override_justification or "",
        }
        for r in q.all()
    ]
    if format == "pdf":
        return _pdf_response_stub("Govt Verification Report", rows)
    return _csv_response(rows, "govt_verification.csv")


@router.get("/str-log")
def report_str_log(
    format: str = Query("csv", regex="^(csv|pdf)$"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(REPORT_READ)),
):
    from app.models.compliance import StrRecord
    q = db.query(StrRecord).filter(StrRecord.tenant_id == tenant.id)
    if date_from:
        q = q.filter(StrRecord.created_at >= date_from)
    if date_to:
        q = q.filter(StrRecord.created_at <= date_to)
    rows = [
        {
            "str_reference": r.str_reference,
            "application_id": str(r.application_id),
            "status": str(r.status.value if hasattr(r.status, 'value') else r.status),
            "nature_of_suspicion": (r.nature_of_suspicion or "")[:200],
            "created_at": str(r.created_at),
            "filed_at": str(r.filed_at) if r.filed_at else "",
        }
        for r in q.all()
    ]
    if format == "pdf":
        return _pdf_response_stub("STR Log Report", rows)
    return _csv_response(rows, "str_log.csv")


@router.get("/dha-fines")
def report_dha_fines(
    format: str = Query("csv", regex="^(csv|pdf)$"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(REPORT_READ)),
):
    """DHA fine exposure: members without valid DHA verification."""
    from app.models.compliance import GovtVerificationRecord
    from app.models.member import Member
    q = db.query(Member, GovtVerificationRecord).outerjoin(
        GovtVerificationRecord,
        (GovtVerificationRecord.member_id == Member.id)
        & (GovtVerificationRecord.check_type == 'dha')
        & (GovtVerificationRecord.tenant_id == tenant.id),
    ).filter(Member.tenant_id == tenant.id)
    rows = [
        {
            "member_name": f"{m.first_name} {m.last_name}",
            "member_id": str(m.id),
            "dha_status": str(g.status.value if g and hasattr(g.status, 'value') else (g.status if g else "not_checked")),
            "dob": str(m.date_of_birth) if m.date_of_birth else "",
            "nationality": m.nationality or "",
        }
        for m, g in q.all()
    ]
    if format == "pdf":
        return _pdf_response_stub("DHA Fine Exposure Report", rows)
    return _csv_response(rows, "dha_fines.csv")
