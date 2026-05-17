from pydantic import BaseModel, Field, model_validator
from typing import Any, Optional, List, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int = 1
    has_next: bool = False
    has_prev: bool = False

    @model_validator(mode="after")
    def compute_derived(self) -> "PaginationMeta":
        self.total_pages = max(1, (self.total + self.per_page - 1) // self.per_page)
        self.has_next = self.page < self.total_pages
        self.has_prev = self.page > 1
        return self


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T] = []
    pagination: PaginationMeta
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None
    detail: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    errors: List[ErrorDetail] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page
