from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    method: str = "bank_transfer"
    reference: Optional[str] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None


class PaymentRead(BaseModel):
    id: str
    payment_number: str
    policy_id: str
    amount: Decimal
    status: str
    method: str
    reference: Optional[str] = None
    notes: Optional[str] = None
    paid_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentListResponse(BaseModel):
    id: str
    payment_number: str
    policy_id: str
    amount: Decimal
    status: str
    method: str
    paid_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
