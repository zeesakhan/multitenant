from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator, model_validator
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime, date
from decimal import Decimal
from app.constants.enums import ApplicationStatus, Gender, SponsorType, ExistingHealthInsurance


# ── Loading schemas ────────────────────────────────────────────────────────────

class LoadingCreate(BaseModel):
    member_id: Optional[str] = None
    loading_type: str = Field(..., description="underwriter|bmi|other|tpa|broker|insurer")
    amount: Optional[Decimal] = Field(None, ge=0, description="Flat AED amount")
    percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Percentage of rated premium")
    notes: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def amount_or_percentage(self):
        if self.amount is None and self.percentage is None:
            raise ValueError("Either amount or percentage must be provided")
        return self


class LoadingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    member_id: Optional[str] = None
    loading_type: str
    amount: Optional[Decimal] = None
    percentage: Optional[Decimal] = None
    applied_by: Optional[str] = None
    applied_at: datetime
    notes: Optional[str] = None
    created_at: datetime


# ── Remark schemas ─────────────────────────────────────────────────────────────

class RemarkCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class RemarkRead(BaseModel):
    id: str
    author_id: str
    author_name: str
    author_role: str
    text: str
    created_at: str


# ── Medical questionnaire schema ───────────────────────────────────────────────

class MedicalQuestion(BaseModel):
    question_id: str
    question_text: str
    answer: bool
    details: Optional[str] = Field(None, max_length=1000)


class PregnancyQuestionnaire(BaseModel):
    is_pregnant: bool = False
    weeks: Optional[int] = Field(None, ge=0, le=42)
    expected_delivery: Optional[date] = None
    complications: Optional[str] = Field(None, max_length=500)


# ── Application item schemas ───────────────────────────────────────────────────

class ApplicationItemCreate(BaseModel):
    coverage_id: str = Field(..., min_length=1)
    premium: Optional[Decimal] = Field(None, gt=0)
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


# ── Co-payment config schema ───────────────────────────────────────────────────

class CoPaymentConfig(BaseModel):
    opt_pct: Decimal = Field(Decimal("20.0"), ge=0, le=100)
    opt_max_cap_aed: Decimal = Field(Decimal("50.0"), ge=0)
    pharmacy_pct: Decimal = Field(Decimal("0.0"), ge=0, le=100)
    lab_pct: Decimal = Field(Decimal("0.0"), ge=0, le=100)
    physio_pct: Decimal = Field(Decimal("0.0"), ge=0, le=100)


# ── Application create/update ──────────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    quote_id: Optional[str] = None
    product_id: Optional[str] = None
    plan_id: Optional[str] = None
    customer_email: EmailStr
    customer_name: str = Field(..., min_length=1, max_length=255)
    member_count: int = Field(default=1, ge=1)
    items: Optional[List[ApplicationItemCreate]] = None
    breakdown: Optional[Dict[str, Any]] = None

    # UAE compliance fields
    sponsor_type: Optional[SponsorType] = SponsorType.INDIVIDUAL
    marital_status: Optional[str] = Field(None, max_length=20)
    occupation: Optional[str] = Field(None, max_length=100)
    employer_name: Optional[str] = Field(None, max_length=200)
    trn: Optional[str] = Field(None, max_length=50, description="UAE Tax Registration Number")
    is_diplomatic_passport: bool = False
    is_eid_under_process: bool = False
    existing_health_insurance: Optional[ExistingHealthInsurance] = None
    co_payment_config: Optional[CoPaymentConfig] = None
    cover_amount: Optional[Decimal] = Field(None, ge=0, description="Selected medical cover limit (AED)")


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    breakdown: Optional[Dict[str, Any]] = None
    marital_status: Optional[str] = Field(None, max_length=20)
    occupation: Optional[str] = Field(None, max_length=100)
    employer_name: Optional[str] = Field(None, max_length=200)
    trn: Optional[str] = Field(None, max_length=50)
    sponsor_type: Optional[SponsorType] = None
    existing_health_insurance: Optional[ExistingHealthInsurance] = None
    is_diplomatic_passport: Optional[bool] = None
    is_eid_under_process: Optional[bool] = None
    co_payment_config: Optional[CoPaymentConfig] = None
    cover_amount: Optional[Decimal] = Field(None, ge=0)


# ── Application read ───────────────────────────────────────────────────────────

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
    premium_breakdown: Optional[Dict[str, Any]] = None
    items: List[ApplicationItemRead] = []
    members: List["MemberReadInline"] = []

    # UAE fields
    aml_status: str = "clear"
    aml_risk_score: Optional[Decimal] = None
    govt_check_status: str = "pending"
    sponsor_type: str = "individual"
    marital_status: Optional[str] = None
    occupation: Optional[str] = None
    employer_name: Optional[str] = None
    trn: Optional[str] = None
    existing_health_insurance: Optional[str] = None
    is_diplomatic_passport: bool = False
    is_eid_under_process: bool = False
    cover_amount: Optional[Decimal] = None
    co_payment_config: Optional[Dict[str, Any]] = None
    remarks: Optional[List[Dict[str, Any]]] = None

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
    marital_status: Optional[str] = None
    nationality: Optional[str] = None
    emirates_id: Optional[str] = None
    passport_number: Optional[str] = None


class ApplicationListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    application_number: str
    customer_name: str
    customer_email: str
    status: ApplicationStatus
    aml_status: str = "clear"
    govt_check_status: str = "pending"
    total_premium: Decimal
    member_count: int
    created_at: datetime


class ApplicationSubmitRequest(BaseModel):
    member_data: Optional[List[Dict[str, Any]]] = None
    additional_info: Optional[Dict[str, Any]] = None


class QuoteRequest(BaseModel):
    """Request body to generate a premium quote for an application's members."""
    members: List[Dict[str, Any]] = Field(..., description="List of member factor dicts: age, gender, location, sum_insured")
    cover_amount: Optional[Decimal] = None
    co_payment_config: Optional[CoPaymentConfig] = None


class ModifyCoverageRequest(BaseModel):
    annual_limit: Decimal = Field(..., gt=0, description="New annual limit in AED")
    reason: str = Field(..., min_length=1, max_length=500)
