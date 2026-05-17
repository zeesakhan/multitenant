from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class ClaimCreate(BaseModel):
    policy_id: str
    member_id: Optional[str] = None
    claim_type: str
    incident_date: date
    description: str = Field(..., min_length=10)
    claimed_amount: Decimal = Field(..., gt=0, decimal_places=2)


class ClaimUpdate(BaseModel):
    description: Optional[str] = None
    claimed_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)


class ClaimReview(BaseModel):
    approved_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    rejection_reason: Optional[str] = None


class ClaimRead(BaseModel):
    id: str
    claim_number: str
    policy_id: str
    member_id: Optional[str] = None
    claim_type: str
    status: str
    incident_date: date
    description: str
    claimed_amount: Decimal
    approved_amount: Optional[Decimal] = None
    rejection_reason: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClaimListResponse(BaseModel):
    id: str
    claim_number: str
    policy_id: str
    claim_type: str
    status: str
    claimed_amount: Decimal
    approved_amount: Optional[Decimal] = None
    incident_date: date
    created_at: datetime

    model_config = {"from_attributes": True}
