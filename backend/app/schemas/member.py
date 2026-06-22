import re
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
from typing import Optional, List, Any, Dict
from datetime import date, datetime
from decimal import Decimal
from app.constants.enums import MemberRelationship, MemberStatus, Gender


EMIRATES_ID_PATTERN = re.compile(r"^784-\d{4}-\d{7}-\d$")


class MedicalAnswerItem(BaseModel):
    question_id: str
    answer: bool
    details: Optional[str] = Field(None, max_length=1000)


class PregnancyQuestionnaire(BaseModel):
    is_pregnant: bool = False
    weeks: Optional[int] = Field(None, ge=0, le=42)
    expected_delivery: Optional[date] = None
    complications: Optional[str] = Field(None, max_length=500)


class MemberCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    relationship: MemberRelationship
    gender: Gender
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    national_id: Optional[str] = Field(None, max_length=100)

    # UAE identity fields
    emirates_id: Optional[str] = Field(None, max_length=25)
    passport_number: Optional[str] = Field(None, max_length=50)
    nationality: Optional[str] = Field(None, max_length=100)
    visa_type: Optional[str] = Field(None, max_length=80)
    document_expiry: Optional[date] = None
    place_of_birth: Optional[str] = Field(None, max_length=100)
    marital_status: Optional[str] = Field(None, max_length=20)

    # Physical / health fields
    height_cm: Optional[Decimal] = Field(None, gt=0, le=300)
    weight_kg: Optional[Decimal] = Field(None, gt=0, le=700)

    # Medical questionnaire (14 yes/no answers)
    medical_questionnaire: Optional[List[MedicalAnswerItem]] = None
    pregnancy_questionnaire: Optional[PregnancyQuestionnaire] = None

    @field_validator("emirates_id")
    @classmethod
    def validate_emirates_id(cls, v):
        if v and not EMIRATES_ID_PATTERN.match(v):
            raise ValueError("Emirates ID must be in format 784-YYYY-NNNNNNN-C")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def not_future_dob(cls, v):
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v


class MemberUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    relationship: Optional[MemberRelationship] = None
    gender: Optional[Gender] = None
    status: Optional[MemberStatus] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    national_id: Optional[str] = Field(None, max_length=100)
    emirates_id: Optional[str] = Field(None, max_length=25)
    passport_number: Optional[str] = Field(None, max_length=50)
    nationality: Optional[str] = Field(None, max_length=100)
    visa_type: Optional[str] = Field(None, max_length=80)
    document_expiry: Optional[date] = None
    place_of_birth: Optional[str] = Field(None, max_length=100)
    marital_status: Optional[str] = Field(None, max_length=20)
    height_cm: Optional[Decimal] = Field(None, gt=0, le=300)
    weight_kg: Optional[Decimal] = Field(None, gt=0, le=700)
    medical_questionnaire: Optional[List[MedicalAnswerItem]] = None
    pregnancy_questionnaire: Optional[PregnancyQuestionnaire] = None

    @field_validator("emirates_id")
    @classmethod
    def validate_emirates_id(cls, v):
        if v and not EMIRATES_ID_PATTERN.match(v):
            raise ValueError("Emirates ID must be in format 784-YYYY-NNNNNNN-C")
        return v


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    relationship: MemberRelationship
    gender: Gender
    status: MemberStatus
    email: Optional[str] = None
    phone: Optional[str] = None
    national_id: Optional[str] = None
    emirates_id: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    visa_type: Optional[str] = None
    document_expiry: Optional[date] = None
    place_of_birth: Optional[str] = None
    marital_status: Optional[str] = None
    height_cm: Optional[Decimal] = None
    weight_kg: Optional[Decimal] = None
    medical_questionnaire: Optional[List[Dict[str, Any]]] = None
    pregnancy_questionnaire: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
