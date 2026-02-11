"""
DOER Platform - SQLAlchemy Database Models

This module defines all database models for the land dispute resolution platform.
Models use async-compatible SQLAlchemy 2.0 patterns.

PRODUCTION NOTES:
- Add database indexes for frequently queried fields
- Consider table partitioning for large datasets
- Add audit logging with triggers or application-level tracking
- Implement soft deletes with is_deleted flag (already included)
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


# Enums for type safety
class UserRole(str, enum.Enum):
    """User roles in the system."""
    CLIENT = "client"
    ADMIN = "admin"
    LEGAL_TALENT = "legal_talent"
    SUPPORT = "support"


class CaseStatus(str, enum.Enum):
    """Status of a land dispute case."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    IN_PROGRESS = "in_progress"
    PENDING_DOCUMENTS = "pending_documents"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class CasePriority(str, enum.Enum):
    """Priority level for cases."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, enum.Enum):
    """Status of workflow tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class DocumentType(str, enum.Enum):
    """Types of uploaded documents."""
    LAND_DEED = "land_deed"
    SURVEY_REPORT = "survey_report"
    COURT_ORDER = "court_order"
    TAX_RECEIPT = "tax_receipt"
    IDENTITY_PROOF = "identity_proof"
    PHOTOGRAPH = "photograph"
    CORRESPONDENCE = "correspondence"
    OTHER = "other"


# ==============================================================================
# USER MODEL
# ==============================================================================

class User(Base):
    """
    User account model for all platform users.
    
    Supports multiple roles: clients, admins, legal professionals, support staff.
    
    PRODUCTION:
    - Add email verification fields (is_email_verified, verification_token)
    - Add phone verification for WhatsApp/SMS
    - Consider OAuth integration columns
    - Add 2FA secret field
    """
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), 
        default=UserRole.CLIENT
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    cases: Mapped[List["Case"]] = relationship(
        "Case",
        back_populates="user",
        foreign_keys="Case.user_id"
    )
    uploaded_documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="uploaded_by_user"
    )
    assigned_tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="assigned_user"
    )
    legal_profile: Mapped[Optional["LegalTalent"]] = relationship(
        "LegalTalent",
        back_populates="user",
        uselist=False
    )
    
    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"


# ==============================================================================
# CASE MODEL
# ==============================================================================

class Case(Base):
    """
    Land dispute case model.
    
    Tracks all aspects of a land dispute from submission to resolution.
    
    PRODUCTION:
    - Add GIS/location fields (latitude, longitude, polygon for land boundaries)
    - Add blockchain hash for document authenticity
    - Consider separate CaseHistory table for audit trail
    - Add full-text search on description and notes
    """
    __tablename__ = "cases"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    # Case details
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    
    # Location information
    # PRODUCTION: Add PostGIS geometry column for accurate land mapping
    land_location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), default="")
    survey_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    land_area_sqft: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Status tracking
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus),
        default=CaseStatus.DRAFT,
        index=True
    )
    priority: Mapped[CasePriority] = mapped_column(
        Enum(CasePriority),
        default=CasePriority.MEDIUM
    )
    
    # User relationships
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id"), 
        index=True
    )
    assigned_talent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("legal_talent.id"),
        nullable=True
    )
    
    # AI Analysis results (stored as JSON string for SQLite compatibility)
    # PRODUCTION: Use JSONB column type in PostgreSQL
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="cases", foreign_keys=[user_id])
    assigned_talent: Mapped[Optional["LegalTalent"]] = relationship(
        "LegalTalent",
        back_populates="assigned_cases"
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="case",
        cascade="all, delete-orphan"
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="case",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Case {self.case_number}: {self.title[:30]}>"


# ==============================================================================
# DOCUMENT MODEL
# ==============================================================================

class Document(Base):
    """
    Document storage model for case-related files.
    
    Stores metadata about uploaded documents. Actual files are stored
    in local filesystem (development) or S3 (production).
    
    PRODUCTION:
    - Add virus scan status field
    - Add OCR extracted text for searchability
    - Add document classification via AI
    - Store S3 version ID for versioning
    """
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # File information
    filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))  # Local path or S3 key
    file_size: Mapped[int] = mapped_column(Integer)  # Size in bytes
    mime_type: Mapped[str] = mapped_column(String(100))
    
    # Document categorization
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType),
        default=DocumentType.OTHER
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cases.id"),
        index=True
    )
    uploaded_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id")
    )
    
    # AI Processing status
    # PRODUCTION: Consider separate DocumentAnalysis table
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="documents")
    uploaded_by_user: Mapped["User"] = relationship("User", back_populates="uploaded_documents")
    
    def __repr__(self):
        return f"<Document {self.filename} ({self.document_type.value})>"


# ==============================================================================
# TASK MODEL
# ==============================================================================

class Task(Base):
    """
    Workflow task model for case management.
    
    Tasks represent discrete work items that need to be completed
    as part of case resolution.
    
    PRODUCTION:
    - Add task dependencies (depends_on field)
    - Add SLA tracking (due date alerts)
    - Consider Celery integration for automated task creation
    - Add task templates for common workflows
    """
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        index=True
    )
    
    # Timing
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Priority (inherits from case but can be overridden)
    priority: Mapped[CasePriority] = mapped_column(
        Enum(CasePriority),
        default=CasePriority.MEDIUM
    )
    
    # Relationships
    case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cases.id"),
        index=True
    )
    assigned_to: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="tasks")
    assigned_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="assigned_tasks"
    )
    
    def __repr__(self):
        return f"<Task {self.title[:30]} ({self.status.value})>"


# ==============================================================================
# LEGAL TALENT MODEL
# ==============================================================================

class LegalTalent(Base):
    """
    Legal professional profile model.
    
    Extends User with specialized fields for legal professionals
    who can be assigned to cases.
    
    PRODUCTION:
    - Add verification status (bar registration, credentials)
    - Add rating/review system
    - Add availability calendar integration
    - Add payment/billing relationship
    """
    __tablename__ = "legal_talent"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Link to user account
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        unique=True
    )
    
    # Professional information
    specialization: Mapped[str] = mapped_column(String(255))
    bar_registration_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    
    # Expertise areas (comma-separated for SQLite)
    # PRODUCTION: Use PostgreSQL array type or separate junction table
    expertise_areas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Pricing
    hourly_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Availability
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    max_active_cases: Mapped[int] = mapped_column(Integer, default=10)
    
    # Performance metrics
    total_cases_handled: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Bio and profile
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    languages: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Location (for matching with nearby cases)
    service_districts: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="legal_profile")
    assigned_cases: Mapped[List["Case"]] = relationship(
        "Case",
        back_populates="assigned_talent"
    )
    
    def __repr__(self):
        return f"<LegalTalent {self.user.full_name if self.user else 'Unknown'} - {self.specialization}>"
