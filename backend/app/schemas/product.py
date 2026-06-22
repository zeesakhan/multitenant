from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from app.constants.enums import ProductStatus, PlanType, CoverageType


class CoverageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    coverage_type: CoverageType
    limit_amount: Optional[Decimal] = None
    copay: Optional[Decimal] = None
    coinsurance_percent: Optional[Decimal] = None
    config: Optional[Dict[str, Any]] = None


class CoverageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    coverage_type: CoverageType
    limit_amount: Optional[Decimal] = None
    copay: Optional[Decimal] = None
    coinsurance_percent: Optional[Decimal] = None
    config: Optional[Dict[str, Any]] = None


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    name: str
    code: str
    plan_type: PlanType
    base_premium: Decimal
    description: Optional[str] = None
    coverage_details: Optional[Dict[str, Any]] = None
    included_services: Optional[Dict[str, Any]] = None
    exclusions: Optional[Dict[str, Any]] = None
    is_active: bool
    coverages: List[CoverageRead] = []
    created_at: datetime
    updated_at: datetime


class PlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=100)
    plan_type: PlanType = PlanType.INDIVIDUAL
    base_premium: Decimal = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    coverage_details: Optional[Dict[str, Any]] = None
    included_services: Optional[Dict[str, Any]] = None
    exclusions: Optional[Dict[str, Any]] = None
    is_active: bool = True


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    plan_type: Optional[PlanType] = None
    base_premium: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=1000)
    coverage_details: Optional[Dict[str, Any]] = None
    included_services: Optional[Dict[str, Any]] = None
    exclusions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    description: Optional[str] = None
    status: ProductStatus
    config: Optional[Dict[str, Any]] = None
    plans: List[PlanRead] = []
    created_at: datetime
    updated_at: datetime


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: ProductStatus = ProductStatus.DRAFT
    config: Optional[Dict[str, Any]] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ProductStatus] = None
    config: Optional[Dict[str, Any]] = None
