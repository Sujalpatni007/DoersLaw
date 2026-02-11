"""
DOER Platform - Tasks Router

Handles workflow tasks for case management.

PRODUCTION UPGRADES:
- Add task dependencies (depends_on field)
- Integrate with calendar for due date reminders
- Celery integration for automated task creation
- SLA tracking and escalation alerts
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Task, Case, User, TaskStatus, UserRole
from app.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse, MessageResponse
)
from app.services.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new task for a case.
    
    Only case owners, admins, and assigned legal talent can create tasks.
    
    PRODUCTION:
    - Send notification to assigned user
    - Add to calendar integration
    """
    # Verify case exists and user has access
    result = await db.execute(
        select(Case)
        .where(Case.id == task_data.case_id)
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
            detail="You don't have access to this case"
        )
    
    task = Task(
        title=task_data.title,
        description=task_data.description,
        due_date=task_data.due_date,
        priority=task_data.priority,
        status=TaskStatus.PENDING,
        case_id=task_data.case_id,
        assigned_to=task_data.assigned_to,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # PRODUCTION: Notify assigned user
    # if task.assigned_to:
    #     await notify_user(task.assigned_to, f"New task assigned: {task.title}")
    
    return task


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[TaskStatus] = None,
    assigned_to_me: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List tasks accessible to the current user.
    
    - Use `assigned_to_me=true` to see only your assigned tasks
    - Clients see tasks for their cases
    - Staff see all tasks or filtered by assignment
    """
    # Base query - join with cases to filter appropriately
    query = select(Task).join(Case).where(Case.is_deleted == False)
    
    if current_user.role == UserRole.CLIENT:
        # Clients see tasks for their cases only
        query = query.where(Case.user_id == current_user.id)
    elif assigned_to_me:
        # Filter to tasks assigned to current user
        query = query.where(Task.assigned_to == current_user.id)
    
    # Apply status filter
    if status:
        query = query.where(Task.status == status)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=total
    )


@router.get("/case/{case_id}", response_model=TaskListResponse)
async def list_case_tasks(
    case_id: int,
    status: Optional[TaskStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all tasks for a specific case.
    """
    # Verify case access
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
    
    if current_user.role == UserRole.CLIENT and case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this case"
        )
    
    # Build query
    query = select(Task).where(Task.case_id == case_id)
    
    if status:
        query = query.where(Task.status == status)
    
    query = query.order_by(Task.due_date.asc().nullslast())
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=len(tasks)
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific task by ID.
    """
    result = await db.execute(
        select(Task)
        .join(Case)
        .where(Task.id == task_id)
        .where(Case.is_deleted == False)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verify access via case
    result = await db.execute(select(Case).where(Case.id == task.case_id))
    case = result.scalar_one_or_none()
    
    if current_user.role == UserRole.CLIENT and case and case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this task"
        )
    
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a task.
    
    Can update status, description, assignment, due date, etc.
    
    PRODUCTION:
    - Log status changes for audit
    - Notify assignee on reassignment
    - Update SLA tracking
    """
    result = await db.execute(
        select(Task)
        .join(Case)
        .where(Task.id == task_id)
        .where(Case.is_deleted == False)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verify access via case
    result = await db.execute(select(Case).where(Case.id == task.case_id))
    case = result.scalar_one_or_none()
    
    if current_user.role == UserRole.CLIENT and case and case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this task"
        )
    
    # Update fields
    update_data = task_update.model_dump(exclude_unset=True)
    old_status = task.status
    
    for field, value in update_data.items():
        setattr(task, field, value)
    
    # Set completed timestamp if completing the task
    if task_update.status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
        task.completed_at = datetime.utcnow()
    
    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)
    
    return task


@router.delete("/{task_id}", response_model=MessageResponse)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a task.
    
    Tasks can be deleted by case owners, assigned users, or admins.
    """
    result = await db.execute(
        select(Task)
        .join(Case)
        .where(Task.id == task_id)
        .where(Case.is_deleted == False)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Verify access
    result = await db.execute(select(Case).where(Case.id == task.case_id))
    case = result.scalar_one_or_none()
    
    can_delete = (
        current_user.role in [UserRole.ADMIN, UserRole.SUPPORT] or
        (case and case.user_id == current_user.id) or
        task.assigned_to == current_user.id
    )
    
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this task"
        )
    
    await db.delete(task)
    await db.commit()
    
    return MessageResponse(
        message="Task deleted successfully",
        success=True
    )
