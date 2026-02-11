"""
DOER Platform - Legal Talent Router

Handles legal professional profiles, matching, and case assignment.

PRODUCTION UPGRADES:
- Add recommendation algorithm for talent matching
- Integrate rating/review system
- Add availability calendar integration
- Payment/billing integration
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import LegalTalent, User, Case, UserRole
from app.schemas import (
    LegalTalentCreate, LegalTalentUpdate, LegalTalentResponse,
    LegalTalentListResponse, CaseAssignment, CaseResponse, MessageResponse
)
from app.services.auth import get_current_user, require_role

router = APIRouter(prefix="/talent", tags=["Legal Talent"])


@router.get("", response_model=LegalTalentListResponse)
async def list_talent(
    specialization: Optional[str] = None,
    available_only: bool = True,
    min_experience: Optional[int] = None,
    district: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List available legal professionals.
    
    Filter by specialization, experience, availability, and location.
    
    PRODUCTION:
    - Add smart matching based on case details
    - Include ratings and reviews
    - Sort by relevance score
    """
    query = select(LegalTalent).options(selectinload(LegalTalent.user))
    
    # Apply filters
    if available_only:
        query = query.where(LegalTalent.is_available == True)
    
    if specialization:
        query = query.where(LegalTalent.specialization.ilike(f"%{specialization}%"))
    
    if min_experience:
        query = query.where(LegalTalent.experience_years >= min_experience)
    
    if district:
        query = query.where(LegalTalent.service_districts.ilike(f"%{district}%"))
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Pagination
    query = query.order_by(LegalTalent.experience_years.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    talent = result.scalars().all()
    
    return LegalTalentListResponse(
        talent=[LegalTalentResponse.model_validate(t) for t in talent],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{talent_id}", response_model=LegalTalentResponse)
async def get_talent(
    talent_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a legal professional.
    """
    result = await db.execute(
        select(LegalTalent)
        .options(selectinload(LegalTalent.user))
        .where(LegalTalent.id == talent_id)
    )
    talent = result.scalar_one_or_none()
    
    if not talent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legal talent profile not found"
        )
    
    return talent


@router.post("", response_model=LegalTalentResponse, status_code=status.HTTP_201_CREATED)
async def create_talent_profile(
    talent_data: LegalTalentCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a legal talent profile (Admin only).
    
    The associated user account must already exist and be set to LEGAL_TALENT role.
    
    PRODUCTION:
    - Add verification workflow
    - Validate bar registration number
    - Background check integration
    """
    # Verify user exists and doesn't have a profile already
    result = await db.execute(
        select(User).where(User.id == talent_data.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.role != UserRole.LEGAL_TALENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must have LEGAL_TALENT role"
        )
    
    # Check for existing profile
    result = await db.execute(
        select(LegalTalent).where(LegalTalent.user_id == talent_data.user_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a legal talent profile"
        )
    
    talent = LegalTalent(
        user_id=talent_data.user_id,
        specialization=talent_data.specialization,
        bar_registration_number=talent_data.bar_registration_number,
        experience_years=talent_data.experience_years,
        expertise_areas=talent_data.expertise_areas,
        hourly_rate=talent_data.hourly_rate,
        bio=talent_data.bio,
        languages=talent_data.languages,
        service_districts=talent_data.service_districts,
        is_available=True,
        is_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(talent)
    await db.commit()
    await db.refresh(talent)
    
    return talent


@router.put("/{talent_id}", response_model=LegalTalentResponse)
async def update_talent_profile(
    talent_id: int,
    talent_update: LegalTalentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a legal talent profile.
    
    Talent can update their own profile. Admins can update any profile.
    """
    result = await db.execute(
        select(LegalTalent)
        .options(selectinload(LegalTalent.user))
        .where(LegalTalent.id == talent_id)
    )
    talent = result.scalar_one_or_none()
    
    if not talent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legal talent profile not found"
        )
    
    # Check permissions
    if (current_user.role != UserRole.ADMIN and 
        talent.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    # Update fields
    update_data = talent_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(talent, field, value)
    
    talent.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(talent)
    
    return talent


@router.post("/cases/{case_id}/assign", response_model=CaseResponse)
async def assign_talent_to_case(
    case_id: int,
    assignment: CaseAssignment,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPPORT)),
    db: AsyncSession = Depends(get_db)
):
    """
    Assign a legal talent to a case (Admin/Support only).
    
    PRODUCTION:
    - Notify both case owner and assigned talent
    - Update availability count
    - Create initial task set based on case type
    """
    # Verify case exists
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
    
    # Verify talent exists and is available
    result = await db.execute(
        select(LegalTalent).where(LegalTalent.id == assignment.talent_id)
    )
    talent = result.scalar_one_or_none()
    
    if not talent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legal talent not found"
        )
    
    if not talent.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Legal talent is not available for new cases"
        )
    
    # Check active case count
    result = await db.execute(
        select(func.count())
        .select_from(Case)
        .where(Case.assigned_talent_id == talent.id)
        .where(Case.status.not_in(['resolved', 'closed']))
        .where(Case.is_deleted == False)
    )
    active_cases = result.scalar()
    
    if active_cases >= talent.max_active_cases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Talent has reached maximum active cases ({talent.max_active_cases})"
        )
    
    # Assign talent
    case.assigned_talent_id = talent.id
    case.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(case)
    
    # PRODUCTION: Send notifications
    # await notify_case_assignment(case.user.phone, talent.user.full_name, case.case_number)
    # await notify_talent_assignment(talent.user.email, case.case_number)
    
    return case


@router.post("/cases/{case_id}/unassign", response_model=CaseResponse)
async def unassign_talent_from_case(
    case_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove talent assignment from a case (Admin only).
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
    
    if not case.assigned_talent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case has no assigned talent"
        )
    
    case.assigned_talent_id = None
    case.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(case)
    
    return case


@router.get("/me/profile", response_model=LegalTalentResponse)
async def get_my_talent_profile(
    current_user: User = Depends(require_role(UserRole.LEGAL_TALENT)),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current user's legal talent profile.
    """
    result = await db.execute(
        select(LegalTalent)
        .where(LegalTalent.user_id == current_user.id)
    )
    talent = result.scalar_one_or_none()
    
    if not talent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a legal talent profile"
        )
    
    return talent
