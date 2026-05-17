from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, require_permissions, get_current_user
from app.services.tenant_service import TenantService
from app.schemas.tenant import BrandConfigUpdate
from app.constants.permissions import BRANDING_READ, BRANDING_UPDATE
from app.utils.formatters import api_response

router = APIRouter(prefix="/branding", tags=["Branding"])


@router.get("/config", response_model=dict)
def get_brand_config(
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions([BRANDING_READ])),
):
    svc = TenantService(db)
    brand = svc.get_brand_config(current_user.tenant_id)
    return api_response(data={
        "id": brand.id,
        "tenant_id": brand.tenant_id,
        "logo_url": brand.logo_url,
        "primary_color": brand.primary_color,
        "secondary_color": brand.secondary_color,
        "accent_color": brand.accent_color,
        "font_family": brand.font_family,
        "company_name": brand.company_name,
        "tagline": brand.tagline,
        "support_email": brand.support_email,
        "support_phone": brand.support_phone,
        "custom_css": brand.custom_css,
        "extra_config": brand.extra_config,
    })


@router.put("/config", response_model=dict)
def update_brand_config(
    payload: BrandConfigUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions([BRANDING_UPDATE])),
):
    svc = TenantService(db)
    brand = svc.update_brand_config(current_user.tenant_id, payload)
    return api_response(data={"id": brand.id, "primary_color": brand.primary_color}, message="Branding updated.")
