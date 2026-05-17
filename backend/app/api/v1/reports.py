from fastapi import APIRouter, Depends, Query
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
