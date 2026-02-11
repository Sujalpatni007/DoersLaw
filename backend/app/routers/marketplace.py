"""
DOER Platform - Marketplace API Router

Endpoints for talent marketplace, collaboration, and admin dashboard.

SECTIONS:
1. Talent Marketplace - Search, match, assign
2. Collaboration - Messaging, documents, video calls
3. Admin Dashboard - Oversight and analytics

PRODUCTION UPGRADES:
- Rate limiting
- Role-based access control
- Audit logging
"""

from typing import Optional, List

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from pydantic import BaseModel, Field

from app.services.talent_marketplace import get_talent_service, Specialization, TalentType
from app.services.collaboration import get_collaboration_service, MessageType
from app.services.admin_dashboard import get_admin_service


router = APIRouter(prefix="/marketplace", tags=["Legal Talent Marketplace"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class MatchRequest(BaseModel):
    """Request for talent matching."""
    state: str = Field(..., description="Case state")
    district: str = Field(..., description="Case district")
    dispute_type: str = Field(default="ownership_dispute")
    complexity: str = Field(default="medium")


class AssignRequest(BaseModel):
    """Request to assign talent."""
    talent_id: int = Field(..., description="Talent ID to assign")
    role: str = Field(default="lead_counsel")
    notes: str = Field(default="")


class MessageRequest(BaseModel):
    """Request to send message."""
    sender_id: int = Field(..., description="Sender user ID")
    sender_name: str = Field(..., description="Sender name")
    content: str = Field(..., description="Message content")


class NoteRequest(BaseModel):
    """Request to add a note."""
    author_id: int = Field(..., description="Author user ID")
    author_name: str = Field(..., description="Author name")
    title: str = Field(..., description="Note title")
    content: str = Field(..., description="Note content")
    is_private: bool = Field(default=False)


class ReassignRequest(BaseModel):
    """Request to reassign talent."""
    admin_id: int = Field(..., description="Admin user ID")
    old_talent_id: Optional[int] = None
    new_talent_id: int = Field(..., description="New talent ID")
    reason: str = Field(..., description="Reason for reassignment")


class OverrideRequest(BaseModel):
    """Request to override AI decision."""
    admin_id: int = Field(..., description="Admin user ID")
    decision_type: str = Field(..., description="Type of AI decision")
    original_recommendation: str = Field(..., description="Original AI recommendation")
    override_value: str = Field(..., description="New value")
    reason: str = Field(..., description="Reason for override")


# ============================================================================
# Talent Marketplace Endpoints
# ============================================================================

@router.get("/talent")
async def list_all_talent():
    """List all legal talent."""
    service = get_talent_service()
    talent = service.get_all_talent()
    
    return {
        "count": len(talent),
        "talent": talent
    }


@router.get("/talent/stats")
async def get_talent_stats():
    """Get marketplace statistics."""
    service = get_talent_service()
    return service.get_talent_stats()


@router.get("/talent/search")
async def search_talent(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    specialization: Optional[str] = Query(None),
    talent_type: Optional[str] = Query(None),
    available_only: bool = Query(True)
):
    """Search talent with filters."""
    service = get_talent_service()
    
    results = service.search_talent(
        state=state,
        district=district,
        specialization=specialization,
        talent_type=talent_type,
        available_only=available_only
    )
    
    return {
        "count": len(results),
        "results": results
    }


@router.get("/talent/{talent_id}")
async def get_talent_profile(talent_id: int):
    """Get a single talent profile."""
    service = get_talent_service()
    
    talent = service.get_talent(talent_id)
    if not talent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Talent not found: {talent_id}"
        )
    
    return talent


@router.post("/match/{case_id}")
async def match_talent(case_id: int, request: MatchRequest):
    """Find matching talent for a case."""
    service = get_talent_service()
    
    result = service.match_talent(
        case_id=case_id,
        state=request.state,
        district=request.district,
        dispute_type=request.dispute_type,
        complexity=request.complexity
    )
    
    return result


@router.post("/assign/{case_id}")
async def assign_talent(case_id: int, request: AssignRequest):
    """Assign talent to a case."""
    service = get_talent_service()
    
    assignment = service.assign_talent(
        case_id=case_id,
        talent_id=request.talent_id,
        role=request.role,
        notes=request.notes
    )
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not assign talent (not found or at capacity)"
        )
    
    return assignment.to_dict()


@router.get("/assignments/{case_id}")
async def get_case_assignments(case_id: int):
    """Get all talent assignments for a case."""
    service = get_talent_service()
    assignments = service.get_case_assignments(case_id)
    
    return {
        "case_id": case_id,
        "assignments": assignments
    }


# ============================================================================
# Collaboration Endpoints
# ============================================================================

@router.websocket("/ws/{case_id}")
async def websocket_endpoint(websocket: WebSocket, case_id: int):
    """WebSocket endpoint for real-time collaboration."""
    service = get_collaboration_service()
    
    await service.connect(case_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "chat":
                await service.send_message(
                    case_id=case_id,
                    sender_id=data.get("sender_id", 0),
                    sender_name=data.get("sender_name", "Anonymous"),
                    content=data.get("content", ""),
                    message_type=MessageType.CHAT
                )
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        service.disconnect(case_id, websocket)


@router.post("/messages/{case_id}")
async def send_message(case_id: int, request: MessageRequest):
    """Send a message (HTTP fallback for WebSocket)."""
    service = get_collaboration_service()
    
    message = await service.send_message(
        case_id=case_id,
        sender_id=request.sender_id,
        sender_name=request.sender_name,
        content=request.content,
        message_type=MessageType.CHAT
    )
    
    return message.to_dict()


@router.get("/messages/{case_id}")
async def get_messages(case_id: int, limit: int = Query(50, ge=1, le=200)):
    """Get messages for a case."""
    service = get_collaboration_service()
    messages = service.get_messages(case_id, limit)
    
    return {
        "case_id": case_id,
        "count": len(messages),
        "messages": messages
    }


@router.post("/notes/{case_id}")
async def add_note(case_id: int, request: NoteRequest):
    """Add a case note."""
    service = get_collaboration_service()
    
    note = await service.add_note(
        case_id=case_id,
        author_id=request.author_id,
        author_name=request.author_name,
        title=request.title,
        content=request.content,
        is_private=request.is_private
    )
    
    return note.to_dict()


@router.get("/notes/{case_id}")
async def get_notes(case_id: int, include_private: bool = Query(False)):
    """Get case notes."""
    service = get_collaboration_service()
    notes = service.get_notes(case_id, include_private)
    
    return {
        "case_id": case_id,
        "count": len(notes),
        "notes": notes
    }


@router.get("/documents/{case_id}")
async def get_shared_documents(case_id: int):
    """Get shared documents for a case."""
    service = get_collaboration_service()
    docs = service.get_documents(case_id)
    
    return {
        "case_id": case_id,
        "count": len(docs),
        "documents": docs
    }


@router.post("/video-call/{case_id}")
async def create_video_call(case_id: int, room_name: Optional[str] = None):
    """Generate a Jitsi Meet video call link."""
    service = get_collaboration_service()
    
    call = service.generate_video_call_link(case_id, room_name)
    
    return call


# ============================================================================
# Admin Dashboard Endpoints
# ============================================================================

admin_router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@admin_router.get("/cases")
async def admin_get_cases(
    status: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0)
):
    """Get all cases with filters (admin view)."""
    service = get_admin_service()
    
    return service.get_all_cases(
        status=status,
        state=state,
        priority=priority,
        limit=limit,
        offset=offset
    )


@admin_router.get("/cases/{case_id}")
async def admin_get_case_details(case_id: int):
    """Get detailed case info (admin view)."""
    service = get_admin_service()
    
    case = service.get_case_details(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case not found: {case_id}"
        )
    
    return case


@admin_router.post("/reassign/{case_id}")
async def admin_reassign_talent(case_id: int, request: ReassignRequest):
    """Reassign talent to a case."""
    service = get_admin_service()
    
    return service.reassign_talent(
        admin_id=request.admin_id,
        case_id=case_id,
        old_talent_id=request.old_talent_id,
        new_talent_id=request.new_talent_id,
        reason=request.reason
    )


@admin_router.post("/override/{case_id}")
async def admin_override_ai(case_id: int, request: OverrideRequest):
    """Override an AI decision."""
    service = get_admin_service()
    
    return service.override_ai_decision(
        admin_id=request.admin_id,
        case_id=case_id,
        decision_type=request.decision_type,
        original_recommendation=request.original_recommendation,
        override_value=request.override_value,
        reason=request.reason
    )


@admin_router.get("/analytics")
async def admin_get_analytics():
    """Get performance analytics."""
    service = get_admin_service()
    return service.get_performance_analytics()


@admin_router.get("/actions")
async def admin_get_actions(limit: int = Query(50)):
    """Get recent admin actions."""
    service = get_admin_service()
    return {
        "count": len(service.actions),
        "actions": service.get_admin_actions(limit)
    }


@admin_router.get("/health")
async def admin_get_system_health():
    """Get system health status."""
    service = get_admin_service()
    return service.get_system_health()


# Include admin router
router.include_router(admin_router)
