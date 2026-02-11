"""
Unified Notification Service
Combines SMS, Push, and In-app notifications
Handles offline sync when internet returns
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set
from enum import Enum
import uuid
import logging

logging.basicConfig(level=logging.INFO)
notif_logger = logging.getLogger("NOTIFICATIONS")


class NotificationChannel(str, Enum):
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    EMAIL = "email"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass
class Notification:
    """Unified notification object"""
    id: str
    user_id: int
    phone_number: Optional[str]
    title: str
    body: str
    channels: List[NotificationChannel]
    priority: NotificationPriority
    status: Dict[NotificationChannel, NotificationStatus]
    data: Dict  # Additional payload
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    case_id: Optional[str] = None


@dataclass
class PendingSync:
    """Actions taken offline via SMS that need to sync to app"""
    id: str
    user_id: int
    phone_number: str
    action_type: str  # case_created, status_checked, etc.
    action_data: Dict
    created_at: datetime
    synced: bool = False
    synced_at: Optional[datetime] = None


class UnifiedNotificationService:
    """
    Unified Notification System
    - Sends to multiple channels based on user preferences and connectivity
    - Queues offline actions for sync when internet returns
    - Critical updates always sent via SMS
    """
    
    def __init__(self):
        self.notifications: Dict[str, Notification] = {}
        self.pending_sync: Dict[str, PendingSync] = {}
        self.user_preferences: Dict[int, Dict] = {}  # User notification preferences
        
        # Default preferences
        self.default_preferences = {
            "channels": [NotificationChannel.IN_APP, NotificationChannel.PUSH],
            "sms_for_critical": True,
            "quiet_hours": {"start": 22, "end": 7},
        }
    
    async def send_notification(
        self,
        user_id: int,
        title: str,
        body: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[NotificationChannel]] = None,
        phone_number: Optional[str] = None,
        case_id: Optional[str] = None,
        data: Optional[Dict] = None,
    ) -> Notification:
        """
        Send notification through appropriate channels
        """
        # Get user preferences
        user_prefs = self.user_preferences.get(user_id, self.default_preferences)
        
        # Determine channels
        if channels is None:
            channels = user_prefs.get("channels", [NotificationChannel.IN_APP])
        
        # Always include SMS for critical notifications
        if priority == NotificationPriority.CRITICAL and user_prefs.get("sms_for_critical", True):
            if NotificationChannel.SMS not in channels:
                channels.append(NotificationChannel.SMS)
        
        # Create notification
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            phone_number=phone_number,
            title=title,
            body=body,
            channels=channels,
            priority=priority,
            status={ch: NotificationStatus.PENDING for ch in channels},
            data=data or {},
            created_at=datetime.now(),
            case_id=case_id,
        )
        
        self.notifications[notification.id] = notification
        
        # Send to each channel
        for channel in channels:
            await self._send_to_channel(notification, channel)
        
        return notification
    
    async def _send_to_channel(self, notification: Notification, channel: NotificationChannel):
        """Send notification to specific channel"""
        try:
            if channel == NotificationChannel.SMS:
                await self._send_sms(notification)
            elif channel == NotificationChannel.PUSH:
                await self._send_push(notification)
            elif channel == NotificationChannel.IN_APP:
                await self._send_in_app(notification)
            elif channel == NotificationChannel.EMAIL:
                await self._send_email(notification)
            
            notification.status[channel] = NotificationStatus.SENT
            notif_logger.info(f"✅ Sent {channel.value} notification: {notification.id[:8]}")
            
        except Exception as e:
            notification.status[channel] = NotificationStatus.FAILED
            notif_logger.error(f"❌ Failed {channel.value} notification: {e}")
    
    async def _send_sms(self, notification: Notification):
        """Send via SMS gateway"""
        from app.services.sms_gateway import get_sms_gateway
        
        if not notification.phone_number:
            raise ValueError("Phone number required for SMS")
        
        gateway = get_sms_gateway()
        content = f"{notification.title}\n\n{notification.body}"
        
        # Get or create conversation
        conv_id = gateway.phone_to_conversation.get(notification.phone_number, str(uuid.uuid4()))
        await gateway.send_sms(notification.phone_number, content, conv_id)
    
    async def _send_push(self, notification: Notification):
        """Send push notification (simulation)"""
        notif_logger.info(f"\n📱 PUSH NOTIFICATION")
        notif_logger.info(f"User: {notification.user_id}")
        notif_logger.info(f"Title: {notification.title}")
        notif_logger.info(f"Body: {notification.body}")
        # In production: Use Firebase, OneSignal, etc.
    
    async def _send_in_app(self, notification: Notification):
        """Store in-app notification"""
        notif_logger.info(f"\n💬 IN-APP NOTIFICATION")
        notif_logger.info(f"User: {notification.user_id}")
        notif_logger.info(f"Title: {notification.title}")
        # In production: Store in database, broadcast via WebSocket
    
    async def _send_email(self, notification: Notification):
        """Send email notification (simulation)"""
        notif_logger.info(f"\n📧 EMAIL NOTIFICATION")
        notif_logger.info(f"User: {notification.user_id}")
        notif_logger.info(f"Subject: {notification.title}")
        # In production: Use SendGrid, AWS SES, etc.
    
    async def queue_offline_action(
        self,
        user_id: int,
        phone_number: str,
        action_type: str,
        action_data: Dict,
    ) -> PendingSync:
        """
        Queue an action taken via SMS for sync when internet returns
        """
        sync = PendingSync(
            id=str(uuid.uuid4()),
            user_id=user_id,
            phone_number=phone_number,
            action_type=action_type,
            action_data=action_data,
            created_at=datetime.now(),
        )
        self.pending_sync[sync.id] = sync
        
        notif_logger.info(f"📤 Queued offline action: {action_type} for user {user_id}")
        return sync
    
    async def sync_offline_actions(self, user_id: int) -> List[PendingSync]:
        """
        Sync pending offline actions when user comes online
        Called when app reconnects or user logs in
        """
        synced = []
        
        for sync_id, sync in list(self.pending_sync.items()):
            if sync.user_id == user_id and not sync.synced:
                # Process the action
                await self._process_sync_action(sync)
                sync.synced = True
                sync.synced_at = datetime.now()
                synced.append(sync)
                
                notif_logger.info(f"✅ Synced offline action: {sync.action_type}")
        
        return synced
    
    async def _process_sync_action(self, sync: PendingSync):
        """Process a queued offline action"""
        action_type = sync.action_type
        data = sync.action_data
        
        if action_type == "case_created":
            # Sync new case to app database
            notif_logger.info(f"Syncing new case: {data.get('case_id')}")
        elif action_type == "status_checked":
            # Log analytics
            notif_logger.info(f"Logging status check: {data.get('case_id')}")
        elif action_type == "message_sent":
            # Sync message to app
            notif_logger.info(f"Syncing message from SMS")
        # Add more action types as needed
    
    def get_user_notifications(
        self,
        user_id: int,
        limit: int = 20,
        unread_only: bool = False,
    ) -> List[Notification]:
        """Get notifications for a user"""
        user_notifs = [
            n for n in self.notifications.values()
            if n.user_id == user_id
        ]
        
        if unread_only:
            user_notifs = [
                n for n in user_notifs
                if NotificationStatus.READ not in n.status.values()
            ]
        
        # Sort by created_at descending
        user_notifs.sort(key=lambda x: x.created_at, reverse=True)
        
        return user_notifs[:limit]
    
    def mark_as_read(self, notification_id: str, channel: NotificationChannel = NotificationChannel.IN_APP):
        """Mark notification as read"""
        if notification_id in self.notifications:
            self.notifications[notification_id].status[channel] = NotificationStatus.READ
    
    def set_user_preferences(self, user_id: int, preferences: Dict):
        """Set user notification preferences"""
        self.user_preferences[user_id] = {
            **self.default_preferences,
            **preferences,
        }


# Singleton instance
_notification_service: Optional[UnifiedNotificationService] = None

def get_notification_service() -> UnifiedNotificationService:
    global _notification_service
    if _notification_service is None:
        _notification_service = UnifiedNotificationService()
    return _notification_service
