from pydantic import BaseModel, ConfigDict, Field, EmailStr, model_validator
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime, date
from decimal import Decimal
from app.constants.enums import ApplicationStatus, Gender


class ApplicationItemCreate(BaseModel):
    coverage_id: str = Field(..., min_length=1)
    premium: Optional[Decimal] = Field(None, decimal_places=2, gt=0)
    notes: Optional[str] = Field(None, max_length=1000)


class CoverageInline(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    coverage_type: str


class ApplicationItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    coverage_id: str
    coverage: Optional[CoverageInline] = None
    premium: Decimal
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ApplicationCreate(BaseModel):
    quote_id: Optional[str] = None
    product_id: Optional[str] = None
    plan_id: Optional[str] = None
    customer_email: EmailStr
    customer_name: str = Field(..., min_length=1, max_length=255)
    member_count: int = Field(default=1, ge=1)
    items: Optional[List[ApplicationItemCreate]] = None
    breakdown: Optional[Dict[str, Any]] = None


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    breakdown: Optional[Dict[str, Any]] = None


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_number: str
    quote_id: Optional[str] = None
    product_id: Optional[str] = None
    plan_id: Optional[str] = None
    created_by: Optional[str] = None
    customer_email: str
    customer_name: str
    member_count: int
    total_premium: Decimal
    status: ApplicationStatus
    breakdown: Optional[Dict[str, Any]] = None
    additional_info: Optional[Dict[str, Any]] = None
    items: List[ApplicationItemRead] = []
    members: List["MemberReadInline"] = []
    created_at: datetime
    updated_at: datetime


class MemberReadInline(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: str
    last_name: str
    date_of_birth: date
    relationship: str
    gender: str
    status: str
    email: Optional[str] = None
    phone: Optional[str] = None


class ApplicationListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_number: str
    customer_name: str
    customer_email: str
    status: ApplicationStatus
    total_premium: Decimal
    member_count: int
    created_at: datetime


class ApplicationSubmitRequest(BaseModel):
    member_data: Optional[List[Dict[str, Any]]] = None
    additional_info: Optional[Dict[str, Any]] = None
