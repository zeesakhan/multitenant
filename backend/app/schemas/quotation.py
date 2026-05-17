from pydantic import BaseModel, ConfigDict, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from app.constants.enums import QuoteStatus


class RateCardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    plan_id: str
    effective_date: datetime
    expiry_date: datetime
    rates: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class RateCardCreate(BaseModel):
    product_id: str
    plan_id: str
    effective_date: datetime
    expiry_date: datetime
    rates: Dict[str, Any]


class RateCardUpdate(BaseModel):
    rates: Dict[str, Any]
    expiry_date: Optional[datetime] = None


class QuoteItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    coverage_id: str
    coverage_name: str
    amount: Decimal


class QuoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    quote_number: str
    product_id: str
    plan_id: str
    created_by: Optional[str] = None
    customer_email: str
    customer_name: str
    total_premium: Decimal
    status: QuoteStatus
    breakdown: Optional[Dict[str, Any]] = None
    valid_until: datetime
    created_at: datetime
    updated_at: datetime


class QuoteCreate(BaseModel):
    product_id: str = Field(..., min_length=1)
    plan_id: str = Field(..., min_length=1)
    customer_email: EmailStr
    customer_name: str = Field(..., min_length=1, max_length=255)
    breakdown: Optional[Dict[str, Any]] = None


class QuoteUpdate(BaseModel):
    status: QuoteStatus
    breakdown: Optional[Dict[str, Any]] = None


class QuoteSendRequest(BaseModel):
    recipient_email: Optional[EmailStr] = None
    message: Optional[str] = None


class QuoteListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    quote_number: str
    customer_name: str
    customer_email: str
    status: QuoteStatus
    total_premium: Decimal
    valid_until: datetime
    created_at: datetime
