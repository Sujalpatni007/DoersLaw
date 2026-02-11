"""
DOER Platform - Cases Router

Handles CRUD operations for land dispute cases.

PRODUCTION UPGRADES:
- Add full-text search on case title/description (PostgreSQL ts_vector)
- Implement case history/audit trail
- Add GIS integration for land location queries
- Webhook notifications on status changes
"""

from datetime import datetime
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Case, User, CaseStatus, CasePriority, UserRole
from app.schemas import (
    CaseCreate, CaseUpdate, CaseResponse, CaseListResponse, CaseDetail,
    CaseStatusUpdate, MessageResponse
)
from app.services.auth import get_current_user, require_role

router = APIRouter(prefix="/cases", tags=["Cases"])


def generate_case_number() -> str:
    """
    Generate a unique case number.
    
    Format: DOER-YYYYMMDD-XXXX
    PRODUCTION: Consider using database sequence for guaranteed uniqueness
    """
    date_part = datetime.utcnow().strftime("%Y%m%d")
    unique_part = uuid.uuid4().hex[:6].upper()
    return f"DOER-{date_part}-{unique_part}"


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new land dispute case.
    
    The case starts in DRAFT status. Submit it to begin the review process.
    
    PRODUCTION:
    - Validate land location against GIS database
    - Auto-assign based on district and talent availability
    - Trigger welcome SMS/WhatsApp notification
    """
    case = Case(
        case_number=generate_case_number(),
        title=case_data.title,
        description=case_data.description,
        land_location=case_data.land_location,
        district=case_data.district,
        state=case_data.state,
        survey_number=case_data.survey_number,
        land_area_sqft=case_data.land_area_sqft,
        priority=case_data.priority,
        status=CaseStatus.DRAFT,
        user_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(case)
    await db.commit()
    await db.refresh(case)
    
    return case


@router.get("", response_model=CaseListResponse)
async def list_cases(
    status: Optional[CaseStatus] = None,
    priority: Optional[CasePriority] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List cases accessible to the current user.
    
    - Regular users see only their own cases
    - Admins and legal talent can see all cases
    - Supports filtering by status and priority
    - Results are paginated
    
    PRODUCTION: Add full-text search parameter
    """
    # Build query based on user role
    query = select(Case).where(Case.is_deleted == False)
    
    if current_user.role == UserRole.CLIENT:
        # Clients only see their own cases
        query = query.where(Case.user_id == current_user.id)
    elif current_user.role == UserRole.LEGAL_TALENT:
        # Legal talent sees assigned cases + unassigned cases
        query = query.where(
            (Case.assigned_talent_id == current_user.id) | 
            (Case.assigned_talent_id == None)
        )
    # Admins see all cases (no additional filter)
    
    # Apply filters
    if status:
        query = query.where(Case.status == status)
    if priority:
        query = query.where(Case.priority == priority)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.order_by(Case.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    cases = result.scalars().all()
    
    return CaseListResponse(
        cases=[CaseResponse.model_validate(c) for c in cases],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific case.
    
    Includes related documents, tasks, and assigned talent.
    """
    # Fetch case with relationships
    query = (
        select(Case)
        .options(
            selectinload(Case.user),
            selectinload(Case.documents),
            selectinload(Case.tasks),
            selectinload(Case.assigned_talent)
        )
        .where(Case.id == case_id)
        .where(Case.is_deleted == False)
    )
    
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Check access permissions
    if current_user.role == UserRole.CLIENT and case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this case"
        )
    
    return case


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_update: CaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update case information.
    
    Only the case owner or admins can update case details.
    Some fields may be locked after case is submitted.
    """
    result = await db.execute(
        select(Case)
        .where(Case.id == case_id)
        .where(Case.is_deleted == False)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.CLIENT and case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own cases"
        )
    
    # Update fields
    update_data = case_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    case.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(case)
    
    return case


@router.post("/{case_id}/submit", response_model=CaseResponse)
async def submit_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a draft case for review.
    
    Changes status from DRAFT to SUBMITTED.
    After submission, certain fields become read-only.
    
    PRODUCTION:
    - Validate all required documents are uploaded
    - Trigger AI analysis of case documents
    - Send SMS/email confirmation
    """
    result = await db.execute(
        select(Case)
        .where(Case.id == case_id)
        .where(Case.user_id == current_user.id)
        .where(Case.is_deleted == False)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    if case.status != CaseStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case cannot be submitted. Current status: {case.status.value}"
        )
    
    case.status = CaseStatus.SUBMITTED
    case.submitted_at = datetime.utcnow()
    case.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(case)
    
    # PRODUCTION: Trigger background tasks
    # await trigger_case_review(case.id)
    # await send_submission_notification(case.user.phone, case.case_number)
    
    return case


@router.patch("/{case_id}/status", response_model=CaseResponse)
async def update_case_status(
    case_id: int,
    status_update: CaseStatusUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.LEGAL_TALENT)),
    db: AsyncSession = Depends(get_db)
):
    """
    Update case status (Admin/Legal Talent only).
    
    Used to move cases through the workflow:
    SUBMITTED → UNDER_REVIEW → IN_PROGRESS → RESOLVED → CLOSED
    
    PRODUCTION: Add audit trail logging
    """
    result = await db.execute(
        select(Case)
        .where(Case.id == case_id)
        .where(Case.is_deleted == False)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    old_status = case.status
    case.status = status_update.status
    case.updated_at = datetime.utcnow()
    
    # Set resolved timestamp if case is being resolved
    if status_update.status == CaseStatus.RESOLVED:
        case.resolved_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(case)
    
    # PRODUCTION: Log status change and send notification
    # await log_status_change(case.id, old_status, case.status, current_user.id)
    # await send_status_notification(case.user.phone, case.case_number, case.status)
    
    return case


@router.delete("/{case_id}", response_model=MessageResponse)
async def delete_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a case.
    
    Cases are not permanently deleted to maintain audit trail.
    Only draft cases can be deleted by the owner.
    Admins can delete any case.
    """
    result = await db.execute(
        select(Case)
        .where(Case.id == case_id)
        .where(Case.is_deleted == False)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.CLIENT:
        if case.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own cases"
            )
        if case.status != CaseStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft cases can be deleted by the owner"
            )
    
    # Soft delete
    case.is_deleted = True
    case.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return MessageResponse(
        message=f"Case {case.case_number} has been deleted",
        success=True
    )
