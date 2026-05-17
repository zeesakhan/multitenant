from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import Optional, Any, Dict
from datetime import datetime
from app.constants.enums import TenantStatus


class TenantCreate(BaseModel):
    code: str
    name: str
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    country: Optional[str] = None
    currency: str = "USD"
    timezone: str = "UTC"
    config: Optional[Dict[str, Any]] = None

    @field_validator("code")
    @classmethod
    def code_uppercase(cls, v: str) -> str:
        return v.upper().strip()


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    status: Optional[TenantStatus] = None
    config: Optional[Dict[str, Any]] = None


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    status: TenantStatus
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    country: Optional[str] = None
    currency: str
    timezone: str
    created_at: datetime
    updated_at: datetime


class BrandConfigUpdate(BaseModel):
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    company_name: Optional[str] = None
    tagline: Optional[str] = None
    support_email: Optional[EmailStr] = None
    support_phone: Optional[str] = None
    custom_css: Optional[str] = None
    extra_config: Optional[Dict[str, Any]] = None


class BrandConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    accent_color: str
    font_family: str
    company_name: Optional[str] = None
    tagline: Optional[str] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    custom_css: Optional[str] = None
    extra_config: Optional[Dict[str, Any]] = None
