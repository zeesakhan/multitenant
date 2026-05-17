from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, get_current_user, require_permissions
from app.schemas.base import APIResponse
from app.services.dashboard_service import DashboardService
from app.constants.permissions import DASHBOARD_READ

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=APIResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant=Depends(require_permissions(DASHBOARD_READ)),
):
    service = DashboardService(db)
    stats = service.get_stats(tenant.id)
    return APIResponse(data=stats)
