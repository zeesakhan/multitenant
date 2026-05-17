from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.constants.enums import DocumentType


class DocumentTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=100)
    template_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    required_fields: Optional[List[str]] = None
    mime_types: Optional[List[str]] = None
    max_size_kb: int = Field(default=5120, ge=1)
    is_required: bool = False


class DocumentTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    template_type: str
    description: Optional[str] = None
    required_fields: Optional[List[str]] = None
    mime_types: Optional[List[str]] = None
    max_size_kb: int
    is_required: bool
    created_at: datetime
    updated_at: datetime


class DocumentUploadCreate(BaseModel):
    document_type: DocumentType
    entity_type: str = Field(..., min_length=1, max_length=100)
    entity_id: str = Field(..., min_length=1)


class DocumentUploadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    file_size: int
    mime_type: str
    document_type: DocumentType
    entity_type: str
    entity_id: str
    uploaded_by: Optional[str] = None
    validation_status: str
    validation_errors: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    document_type: DocumentType
    entity_type: str
    entity_id: str
    file_size: int
    validation_status: str
    created_at: datetime


class DocumentTemplateListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    template_type: str
    max_size_kb: int
    is_required: bool
