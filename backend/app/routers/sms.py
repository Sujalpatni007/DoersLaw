"""
SMS Admin Router
API endpoints for SMS management, simulation, and admin panel
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import asyncio

from app.services.sms_gateway import get_sms_gateway, SMSDirection
from app.services.ivr_service import get_ivr_service
from app.services.notification_service import get_notification_service, NotificationChannel, NotificationPriority

router = APIRouter(prefix="/sms", tags=["SMS Gateway"])
admin_router = APIRouter(prefix="/sms/admin", tags=["SMS Admin"])


# =============================================================================
# Request/Response Models
# =============================================================================

class IncomingSMSRequest(BaseModel):
    """Simulate incoming SMS"""
    phone_number: str
    content: str


class OutgoingSMSRequest(BaseModel):
    """Send SMS (admin manual reply)"""
    phone_number: str
    content: str


class BulkSMSRequest(BaseModel):
    """Bulk SMS notification"""
    phone_numbers: List[str]
    message: str


class IVRStartRequest(BaseModel):
    """Start IVR call simulation"""
    phone_number: str


class IVRDTMFRequest(BaseModel):
    """DTMF input for IVR"""
    call_id: str
    digit: str


class NotificationRequest(BaseModel):
    """Send unified notification"""
    user_id: int
    title: str
    body: str
    phone_number: Optional[str] = None
    priority: str = "normal"
    channels: Optional[List[str]] = None
    case_id: Optional[str] = None


# =============================================================================
# SMS Simulation Endpoints
# =============================================================================

@router.post("/simulate/incoming")
async def simulate_incoming_sms(request: IncomingSMSRequest):
    """
    Simulate receiving an SMS from a user.
    Use this to test the full SMS conversation flow.
    """
    gateway = get_sms_gateway()
    message = await gateway.receive_sms(request.phone_number, request.content)
    
    # Get conversation for response
    conversation = gateway.get_conversation_by_phone(request.phone_number)
    
    return {
        "status": "received",
        "message_id": message.id,
        "conversation_id": message.conversation_id,
        "conversation_state": conversation.state.value if conversation else None,
        "response_sent": True,
    }


@router.post("/simulate/outgoing")
async def simulate_outgoing_sms(request: OutgoingSMSRequest):
    """
    Manually send an SMS (admin reply).
    """
    gateway = get_sms_gateway()
    
    # Get or create conversation
    conv_id = gateway.phone_to_conversation.get(request.phone_number)
    if not conv_id:
        # Create new conversation just for sending
        import uuid
        conv_id = str(uuid.uuid4())
    
    message = await gateway.send_sms(request.phone_number, request.content, conv_id)
    
    return {
        "status": "sent",
        "message_id": message.id,
        "phone_number": request.phone_number,
        "content": request.content,
    }


@router.get("/conversation/{phone_number}")
async def get_conversation(phone_number: str):
    """
    Get SMS conversation history for a phone number.
    """
    gateway = get_sms_gateway()
    conversation = gateway.get_conversation_by_phone(phone_number)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation.id,
        "phone_number": conversation.phone_number,
        "state": conversation.state.value,
        "language": conversation.language,
        "case_id": conversation.case_id,
        "messages": [
            {
                "id": msg.id,
                "direction": msg.direction.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in conversation.messages
        ],
        "created_at": conversation.created_at.isoformat(),
        "last_activity": conversation.last_activity.isoformat(),
    }


# =============================================================================
# Admin Panel Endpoints
# =============================================================================

@admin_router.get("/conversations")
async def admin_get_all_conversations():
    """
    Get all SMS conversations for admin panel.
    """
    gateway = get_sms_gateway()
    conversations = gateway.get_all_conversations()
    
    return {
        "total": len(conversations),
        "conversations": [
            {
                "id": conv.id,
                "phone_number": conv.phone_number,
                "state": conv.state.value,
                "language": conv.language,
                "case_id": conv.case_id,
                "message_count": len(conv.messages),
                "last_message": conv.messages[-1].content[:50] + "..." if conv.messages else None,
                "last_activity": conv.last_activity.isoformat(),
            }
            for conv in sorted(conversations, key=lambda x: x.last_activity, reverse=True)
        ],
    }


@admin_router.post("/reply")
async def admin_reply(request: OutgoingSMSRequest):
    """
    Admin manual reply to SMS conversation.
    """
    return await simulate_outgoing_sms(request)


@admin_router.post("/bulk")
async def admin_bulk_sms(request: BulkSMSRequest):
    """
    Send bulk SMS notifications.
    """
    gateway = get_sms_gateway()
    messages = await gateway.send_bulk_notification(request.phone_numbers, request.message)
    
    return {
        "status": "sent",
        "total_sent": len(messages),
        "recipients": request.phone_numbers,
    }


@admin_router.post("/critical-update")
async def send_critical_update(phone_number: str, case_id: str, update: str):
    """
    Send critical case update via SMS.
    """
    gateway = get_sms_gateway()
    await gateway.send_critical_update(phone_number, case_id, update)
    
    return {
        "status": "sent",
        "phone_number": phone_number,
        "case_id": case_id,
    }


# =============================================================================
# IVR Endpoints
# =============================================================================

@router.post("/ivr/start")
async def start_ivr_call(request: IVRStartRequest):
    """
    Start IVR call simulation.
    """
    ivr = get_ivr_service()
    call = await ivr.start_call(request.phone_number)
    
    return {
        "call_id": call.id,
        "phone_number": call.phone_number,
        "state": call.state.value,
        "prompt": "Welcome to DOER. Press 1 for English, 2 for Hindi.",
    }


@router.post("/ivr/dtmf")
async def process_ivr_dtmf(request: IVRDTMFRequest):
    """
    Process IVR DTMF input (phone keypad press).
    """
    ivr = get_ivr_service()
    response = await ivr.process_dtmf(request.call_id, request.digit)
    
    return response


@router.post("/ivr/end/{call_id}")
async def end_ivr_call(call_id: str):
    """
    End IVR call session.
    """
    ivr = get_ivr_service()
    await ivr.end_call(call_id)
    
    return {"status": "ended", "call_id": call_id}


# =============================================================================
# Unified Notification Endpoints
# =============================================================================

@router.post("/notify")
async def send_notification(request: NotificationRequest):
    """
    Send unified notification (SMS + Push + In-app).
    """
    notif_service = get_notification_service()
    
    # Map string channels to enum
    channels = None
    if request.channels:
        channel_map = {
            "sms": NotificationChannel.SMS,
            "push": NotificationChannel.PUSH,
            "in_app": NotificationChannel.IN_APP,
            "email": NotificationChannel.EMAIL,
        }
        channels = [channel_map[ch] for ch in request.channels if ch in channel_map]
    
    # Map priority
    priority_map = {
        "low": NotificationPriority.LOW,
        "normal": NotificationPriority.NORMAL,
        "high": NotificationPriority.HIGH,
        "critical": NotificationPriority.CRITICAL,
    }
    priority = priority_map.get(request.priority, NotificationPriority.NORMAL)
    
    notification = await notif_service.send_notification(
        user_id=request.user_id,
        title=request.title,
        body=request.body,
        priority=priority,
        channels=channels,
        phone_number=request.phone_number,
        case_id=request.case_id,
    )
    
    return {
        "notification_id": notification.id,
        "channels": [ch.value for ch in notification.channels],
        "status": {ch.value: status.value for ch, status in notification.status.items()},
    }


@router.get("/notifications/{user_id}")
async def get_user_notifications(user_id: int, limit: int = 20, unread_only: bool = False):
    """
    Get notifications for a user.
    """
    notif_service = get_notification_service()
    notifications = notif_service.get_user_notifications(user_id, limit, unread_only)
    
    return {
        "total": len(notifications),
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "body": n.body,
                "priority": n.priority.value,
                "case_id": n.case_id,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ],
    }


@router.post("/sync/{user_id}")
async def sync_offline_actions(user_id: int):
    """
    Sync offline actions when user comes online.
    """
    notif_service = get_notification_service()
    synced = await notif_service.sync_offline_actions(user_id)
    
    return {
        "synced_count": len(synced),
        "actions": [
            {
                "id": s.id,
                "action_type": s.action_type,
                "synced_at": s.synced_at.isoformat() if s.synced_at else None,
            }
            for s in synced
        ],
    }


# =============================================================================
# WebSocket for Real-time SMS Updates
# =============================================================================

# Connected admin clients
admin_connections: List[WebSocket] = []


@admin_router.websocket("/ws")
async def sms_admin_websocket(websocket: WebSocket):
    """
    WebSocket for real-time SMS conversation updates.
    Admin panel connects here to see incoming messages live.
    """
    await websocket.accept()
    admin_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive and handle any incoming commands
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
            elif data.startswith("reply:"):
                # Handle reply from admin panel
                parts = data.split(":", 2)
                if len(parts) == 3:
                    phone, content = parts[1], parts[2]
                    gateway = get_sms_gateway()
                    conv_id = gateway.phone_to_conversation.get(phone, "")
                    await gateway.send_sms(phone, content, conv_id)
                    await websocket.send_text(f"sent:{phone}")
                    
    except WebSocketDisconnect:
        admin_connections.remove(websocket)


async def broadcast_sms_update(message: dict):
    """Broadcast SMS update to all connected admin clients"""
    for connection in admin_connections:
        try:
            await connection.send_json(message)
        except:
            pass
