from pydantic import BaseModel, ConfigDict, Field, EmailStr
from typing import Optional
from datetime import date, datetime
from app.constants.enums import MemberRelationship, MemberStatus, Gender


class MemberCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    relationship: MemberRelationship
    gender: Gender
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    national_id: Optional[str] = Field(None, max_length=100)


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
    created_at: datetime
    updated_at: datetime
