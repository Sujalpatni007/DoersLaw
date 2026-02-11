"""
DOER Platform - Collaboration Service

Real-time collaboration using WebSockets.

FEATURES:
- In-app messaging between parties and talent
- Shared document workspace
- Case notes
- Jitsi Meet video call integration

PRODUCTION UPGRADES:
- Redis pub/sub for horizontal scaling
- Message persistence to database
- File upload to cloud storage
- WebRTC for direct video calls
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from enum import Enum
import json
import hashlib

from fastapi import WebSocket


class MessageType(str, Enum):
    """Message types."""
    CHAT = "chat"
    SYSTEM = "system"
    DOCUMENT = "document"
    NOTE = "note"
    VIDEO_CALL = "video_call"


@dataclass
class Message:
    """A collaboration message."""
    message_id: str
    case_id: int
    sender_id: int
    sender_name: str
    message_type: MessageType
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "case_id": self.case_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class SharedDocument:
    """A document shared in case workspace."""
    doc_id: str
    case_id: int
    filename: str
    file_path: str
    uploaded_by: int
    uploaded_at: datetime
    description: str = ""
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "case_id": self.case_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "uploaded_by": self.uploaded_by,
            "uploaded_at": self.uploaded_at.isoformat(),
            "description": self.description,
            "version": self.version
        }


@dataclass
class CaseNote:
    """A case note."""
    note_id: str
    case_id: int
    author_id: int
    author_name: str
    title: str
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_private: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "note_id": self.note_id,
            "case_id": self.case_id,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_private": self.is_private
        }


class CollaborationService:
    """
    Manages real-time collaboration for cases.
    """
    
    def __init__(self):
        """Initialize the collaboration service."""
        # In-memory storage (use Redis in production)
        self.messages: Dict[int, List[Message]] = {}  # case_id -> messages
        self.documents: Dict[int, List[SharedDocument]] = {}  # case_id -> docs
        self.notes: Dict[int, List[CaseNote]] = {}  # case_id -> notes
        
        # Active WebSocket connections per case
        self.connections: Dict[int, Set[WebSocket]] = {}
        
        # Counters
        self.message_counter = 0
        self.doc_counter = 0
        self.note_counter = 0
    
    # =========================================================================
    # WebSocket Connection Management
    # =========================================================================
    
    async def connect(self, case_id: int, websocket: WebSocket):
        """Add a WebSocket connection for a case."""
        await websocket.accept()
        
        if case_id not in self.connections:
            self.connections[case_id] = set()
        
        self.connections[case_id].add(websocket)
        print(f"📡 WebSocket connected for case {case_id} ({len(self.connections[case_id])} active)")
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "case_id": case_id,
            "message": "Connected to case collaboration"
        })
    
    def disconnect(self, case_id: int, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if case_id in self.connections:
            self.connections[case_id].discard(websocket)
            print(f"📡 WebSocket disconnected from case {case_id}")
    
    async def broadcast(self, case_id: int, message: Dict[str, Any], exclude: Optional[WebSocket] = None):
        """Broadcast message to all connections for a case."""
        if case_id not in self.connections:
            return
        
        disconnected = set()
        for connection in self.connections[case_id]:
            if connection != exclude:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.connections[case_id].discard(conn)
    
    # =========================================================================
    # Messaging
    # =========================================================================
    
    async def send_message(
        self,
        case_id: int,
        sender_id: int,
        sender_name: str,
        content: str,
        message_type: MessageType = MessageType.CHAT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Send a message in a case chat."""
        self.message_counter += 1
        
        message = Message(
            message_id=f"MSG-{case_id}-{self.message_counter:06d}",
            case_id=case_id,
            sender_id=sender_id,
            sender_name=sender_name,
            message_type=message_type,
            content=content,
            metadata=metadata or {}
        )
        
        # Store message
        if case_id not in self.messages:
            self.messages[case_id] = []
        self.messages[case_id].append(message)
        
        # Broadcast to all connected clients
        await self.broadcast(case_id, {
            "type": "new_message",
            "message": message.to_dict()
        })
        
        return message
    
    def get_messages(
        self,
        case_id: int,
        limit: int = 50,
        before: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages for a case."""
        messages = self.messages.get(case_id, [])
        
        # Simple pagination - return last N
        return [m.to_dict() for m in messages[-limit:]]
    
    # =========================================================================
    # Document Sharing
    # =========================================================================
    
    async def share_document(
        self,
        case_id: int,
        filename: str,
        file_path: str,
        uploaded_by: int,
        description: str = ""
    ) -> SharedDocument:
        """Share a document in the case workspace."""
        self.doc_counter += 1
        
        doc = SharedDocument(
            doc_id=f"DOC-{case_id}-{self.doc_counter:04d}",
            case_id=case_id,
            filename=filename,
            file_path=file_path,
            uploaded_by=uploaded_by,
            uploaded_at=datetime.utcnow(),
            description=description
        )
        
        if case_id not in self.documents:
            self.documents[case_id] = []
        self.documents[case_id].append(doc)
        
        # Broadcast document addition
        await self.broadcast(case_id, {
            "type": "document_shared",
            "document": doc.to_dict()
        })
        
        return doc
    
    def get_documents(self, case_id: int) -> List[Dict[str, Any]]:
        """Get all shared documents for a case."""
        docs = self.documents.get(case_id, [])
        return [d.to_dict() for d in docs]
    
    # =========================================================================
    # Case Notes
    # =========================================================================
    
    async def add_note(
        self,
        case_id: int,
        author_id: int,
        author_name: str,
        title: str,
        content: str,
        is_private: bool = False
    ) -> CaseNote:
        """Add a note to a case."""
        self.note_counter += 1
        
        note = CaseNote(
            note_id=f"NOTE-{case_id}-{self.note_counter:04d}",
            case_id=case_id,
            author_id=author_id,
            author_name=author_name,
            title=title,
            content=content,
            is_private=is_private
        )
        
        if case_id not in self.notes:
            self.notes[case_id] = []
        self.notes[case_id].append(note)
        
        # Broadcast note (unless private)
        if not is_private:
            await self.broadcast(case_id, {
                "type": "note_added",
                "note": note.to_dict()
            })
        
        return note
    
    def get_notes(self, case_id: int, include_private: bool = False) -> List[Dict[str, Any]]:
        """Get all notes for a case."""
        notes = self.notes.get(case_id, [])
        
        if include_private:
            return [n.to_dict() for n in notes]
        else:
            return [n.to_dict() for n in notes if not n.is_private]
    
    # =========================================================================
    # Video Call (Jitsi Meet)
    # =========================================================================
    
    def generate_video_call_link(
        self,
        case_id: int,
        room_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a Jitsi Meet video call link.
        
        Uses free Jitsi Meet public servers.
        For production, deploy self-hosted Jitsi.
        """
        if room_name is None:
            # Generate unique room name
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M")
            room_hash = hashlib.md5(f"case-{case_id}-{timestamp}".encode()).hexdigest()[:8]
            room_name = f"doer-case-{case_id}-{room_hash}"
        
        # Public Jitsi Meet server
        jitsi_domain = "meet.jit.si"
        
        return {
            "room_name": room_name,
            "meeting_url": f"https://{jitsi_domain}/{room_name}",
            "case_id": case_id,
            "created_at": datetime.utcnow().isoformat(),
            "instructions": {
                "join": "Click the meeting URL to join the video call",
                "share": "Share this link with other participants",
                "features": ["Screen sharing", "Chat", "Recording (optional)"]
            }
        }


# Singleton instance
_service: Optional[CollaborationService] = None


def get_collaboration_service() -> CollaborationService:
    """Get or create the collaboration service."""
    global _service
    if _service is None:
        _service = CollaborationService()
    return _service
