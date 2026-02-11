"""
DOER Platform - Pydantic Schemas

This module defines all request/response schemas for API validation.
Schemas are separate from SQLAlchemy models to maintain clean API contracts.

PRODUCTION:
- Add more specific validation rules (regex for phone, etc.)
- Consider OpenAPI examples for better documentation
- Add rate limiting response schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models import UserRole, CaseStatus, CasePriority, TaskStatus, DocumentType


# ==============================================================================
# AUTHENTICATION SCHEMAS
# ==============================================================================

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str  # User ID
    exp: datetime
    role: str


class TokenRefresh(BaseModel):
    """Request to refresh access token."""
    refresh_token: str


# ==============================================================================
# USER SCHEMAS
# ==============================================================================

class UserBase(BaseModel):
    """Base user fields shared across schemas."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.CLIENT


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)


class UserResponse(UserBase):
    """User data returned in API responses."""
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserBrief(BaseModel):
    """Minimal user info for embedding in other responses."""
    id: int
    full_name: str
    email: EmailStr
    
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# CASE SCHEMAS
# ==============================================================================

class CaseBase(BaseModel):
    """Base case fields."""
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    land_location: Optional[str] = None
    district: Optional[str] = None
    state: str = ""
    survey_number: Optional[str] = None
    land_area_sqft: Optional[float] = Field(None, gt=0)


class CaseCreate(CaseBase):
    """Schema for creating a new case."""
    priority: CasePriority = CasePriority.MEDIUM


class CaseUpdate(BaseModel):
    """Schema for updating a case."""
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    land_location: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    survey_number: Optional[str] = None
    land_area_sqft: Optional[float] = Field(None, gt=0)
    priority: Optional[CasePriority] = None
    status: Optional[CaseStatus] = None


class CaseResponse(CaseBase):
    """Complete case data for API responses."""
    id: int
    case_number: str
    status: CaseStatus
    priority: CasePriority
    user_id: int
    assigned_talent_id: Optional[int] = None
    ai_summary: Optional[str] = None
    ai_recommendations: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class CaseListResponse(BaseModel):
    """Paginated list of cases."""
    cases: List[CaseResponse]
    total: int
    page: int
    page_size: int


class CaseDetail(CaseResponse):
    """Case with related data for detail view."""
    user: UserBrief
    documents: List["DocumentResponse"] = []
    tasks: List["TaskResponse"] = []
    assigned_talent: Optional["LegalTalentBrief"] = None


class CaseStatusUpdate(BaseModel):
    """Schema for updating case status only."""
    status: CaseStatus


# ==============================================================================
# DOCUMENT SCHEMAS
# ==============================================================================

class DocumentBase(BaseModel):
    """Base document fields."""
    document_type: DocumentType = DocumentType.OTHER
    description: Optional[str] = None


class DocumentUpload(DocumentBase):
    """Metadata sent with file upload."""
    case_id: int


class DocumentResponse(DocumentBase):
    """Document data for API responses."""
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    case_id: int
    uploaded_by: int
    is_processed: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """List of documents."""
    documents: List[DocumentResponse]
    total: int


# ==============================================================================
# TASK SCHEMAS
# ==============================================================================

class TaskBase(BaseModel):
    """Base task fields."""
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: CasePriority = CasePriority.MEDIUM


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    case_id: int
    assigned_to: Optional[int] = None


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    priority: Optional[CasePriority] = None
    assigned_to: Optional[int] = None


class TaskResponse(TaskBase):
    """Task data for API responses."""
    id: int
    status: TaskStatus
    case_id: int
    assigned_to: Optional[int] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """List of tasks."""
    tasks: List[TaskResponse]
    total: int


# ==============================================================================
# LEGAL TALENT SCHEMAS
# ==============================================================================

class LegalTalentBase(BaseModel):
    """Base legal talent fields."""
    specialization: str = Field(..., min_length=3, max_length=255)
    experience_years: int = Field(..., ge=0)
    expertise_areas: Optional[str] = None
    hourly_rate: Optional[float] = Field(None, gt=0)
    bio: Optional[str] = None
    languages: Optional[str] = None
    service_districts: Optional[str] = None


class LegalTalentCreate(LegalTalentBase):
    """Schema for creating a legal talent profile."""
    user_id: int
    bar_registration_number: Optional[str] = None


class LegalTalentUpdate(BaseModel):
    """Schema for updating a legal talent profile."""
    specialization: Optional[str] = Field(None, min_length=3, max_length=255)
    experience_years: Optional[int] = Field(None, ge=0)
    expertise_areas: Optional[str] = None
    hourly_rate: Optional[float] = Field(None, gt=0)
    is_available: Optional[bool] = None
    max_active_cases: Optional[int] = Field(None, ge=1)
    bio: Optional[str] = None
    languages: Optional[str] = None
    service_districts: Optional[str] = None


class LegalTalentResponse(LegalTalentBase):
    """Legal talent data for API responses."""
    id: int
    user_id: int
    bar_registration_number: Optional[str] = None
    is_available: bool
    max_active_cases: int
    total_cases_handled: int
    success_rate: Optional[float] = None
    is_verified: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class LegalTalentBrief(BaseModel):
    """Minimal talent info for embedding."""
    id: int
    specialization: str
    experience_years: int
    is_available: bool
    
    model_config = ConfigDict(from_attributes=True)


class LegalTalentListResponse(BaseModel):
    """Paginated list of legal talent."""
    talent: List[LegalTalentResponse]
    total: int
    page: int
    page_size: int


class CaseAssignment(BaseModel):
    """Schema for assigning talent to a case."""
    talent_id: int


# ==============================================================================
# GENERIC RESPONSE SCHEMAS
# ==============================================================================

class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
    error_code: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str


# Forward reference updates for nested schemas
CaseDetail.model_rebuild()
