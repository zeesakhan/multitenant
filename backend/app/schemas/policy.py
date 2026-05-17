from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.constants.enums import PolicyStatus


class PolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    policy_number: str
    application_id: Optional[str] = None
    quote_id: Optional[str] = None
    product_id: str
    plan_id: str
    customer_name: str
    customer_email: str
    member_count: int
    total_premium: Decimal
    status: PolicyStatus
    effective_date: datetime
    expiry_date: datetime
    issued_by: Optional[str] = None
    issued_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PolicyListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    policy_number: str
    customer_name: str
    customer_email: str
    total_premium: Decimal
    status: PolicyStatus
    effective_date: datetime
    expiry_date: datetime
    created_at: datetime
