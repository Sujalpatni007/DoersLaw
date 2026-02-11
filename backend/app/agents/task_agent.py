"""
DOER Platform - Task Automation Agent

Creates tasks, auto-assigns based on workload, sends notifications.

FEATURES:
- Automatic task creation on state transitions
- Workload-based assignment
- Deadline tracking
- Console notifications (Twilio later)
- Event triggers (document upload, response received)

PRODUCTION UPGRADES:
- Twilio SMS/WhatsApp integration
- Email notifications
- Push notifications
- SLA breach alerts
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import asyncio


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Task status values."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class TriggerType(str, Enum):
    """Task trigger types."""
    STATE_TRANSITION = "state_transition"
    TIME_BASED = "time_based"
    DOCUMENT_UPLOAD = "document_upload"
    RESPONSE_RECEIVED = "response_received"
    MANUAL = "manual"


@dataclass
class AgentTask:
    """A task created by the automation agent."""
    task_id: str
    case_id: int
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    trigger: TriggerType
    created_at: datetime
    deadline: datetime
    assigned_to: Optional[int] = None  # User ID
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "case_id": self.case_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "trigger": self.trigger.value,
            "created_at": self.created_at.isoformat(),
            "deadline": self.deadline.isoformat(),
            "assigned_to": self.assigned_to,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata
        }


# Task templates by state
STATE_TASK_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "intake": [
        {"title": "Review Case Submission", "desc": "Review initial case details", "days": 1, "priority": "high"},
        {"title": "Request Missing Documents", "desc": "Identify and request missing docs", "days": 2, "priority": "medium"},
    ],
    "verification": [
        {"title": "Verify Uploaded Documents", "desc": "Run OCR and verification", "days": 2, "priority": "high"},
        {"title": "Cross-check Land Records", "desc": "Verify against Bhulekh", "days": 3, "priority": "high"},
        {"title": "Prepare Verification Report", "desc": "Generate discrepancy report", "days": 1, "priority": "medium"},
    ],
    "analysis": [
        {"title": "Analyze Dispute Details", "desc": "Deep analysis of dispute", "days": 3, "priority": "high"},
        {"title": "Generate Timeline", "desc": "Create case timeline", "days": 1, "priority": "medium"},
        {"title": "Identify Settlement Options", "desc": "Preliminary options", "days": 2, "priority": "medium"},
    ],
    "negotiation": [
        {"title": "Contact All Parties", "desc": "Initial outreach", "days": 2, "priority": "urgent"},
        {"title": "Schedule Mediation", "desc": "Set mediation date", "days": 3, "priority": "high"},
        {"title": "Prepare Settlement Proposals", "desc": "Draft options", "days": 5, "priority": "medium"},
        {"title": "Document Negotiation Progress", "desc": "Track discussions", "days": 7, "priority": "low"},
    ],
    "resolution": [
        {"title": "Draft Settlement Agreement", "desc": "Prepare legal docs", "days": 5, "priority": "urgent"},
        {"title": "Get Party Approvals", "desc": "Collect signatures", "days": 7, "priority": "high"},
        {"title": "Finalize Documentation", "desc": "Complete paperwork", "days": 3, "priority": "medium"},
    ],
    "closure": [
        {"title": "Archive Case Documents", "desc": "Organize final docs", "days": 2, "priority": "medium"},
        {"title": "Send Closure Notification", "desc": "Notify all parties", "days": 1, "priority": "high"},
        {"title": "Update Case Status", "desc": "Mark as closed", "days": 1, "priority": "low"},
    ],
}


# Mock workload data for assignment
MOCK_WORKLOAD: Dict[int, int] = {
    1: 5,   # User 1 has 5 tasks
    2: 3,   # User 2 has 3 tasks
    3: 8,   # User 3 has 8 tasks
    4: 2,   # User 4 has 2 tasks
}


class TaskAutomationAgent:
    """
    Automates task creation, assignment, and notifications.
    """
    
    def __init__(self):
        """Initialize the task automation agent."""
        self.tasks: Dict[str, AgentTask] = {}
        self.task_counter = 0
        self.notifications: List[Dict[str, Any]] = []
    
    def _generate_task_id(self, case_id: int) -> str:
        """Generate a unique task ID."""
        self.task_counter += 1
        return f"TASK-{case_id}-{self.task_counter:04d}"
    
    async def create_tasks_for_state(
        self,
        case_id: int,
        state: str,
        auto_assign: bool = True
    ) -> List[AgentTask]:
        """
        Create tasks when entering a new state.
        
        Args:
            case_id: Case ID
            state: State name
            auto_assign: Whether to auto-assign tasks
            
        Returns:
            List of created tasks
        """
        templates = STATE_TASK_TEMPLATES.get(state.lower(), [])
        created_tasks = []
        
        for template in templates:
            task = AgentTask(
                task_id=self._generate_task_id(case_id),
                case_id=case_id,
                title=template["title"],
                description=template["desc"],
                priority=TaskPriority(template["priority"]),
                status=TaskStatus.PENDING,
                trigger=TriggerType.STATE_TRANSITION,
                created_at=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=template["days"]),
                metadata={"state": state}
            )
            
            # Auto-assign if enabled
            if auto_assign:
                assigned_user = self._get_least_loaded_user()
                task.assigned_to = assigned_user
                task.assigned_at = datetime.utcnow()
                task.status = TaskStatus.ASSIGNED
                
                # Update mock workload
                MOCK_WORKLOAD[assigned_user] = MOCK_WORKLOAD.get(assigned_user, 0) + 1
            
            self.tasks[task.task_id] = task
            created_tasks.append(task)
            
            # Send notification
            await self._send_notification(task, "created")
        
        return created_tasks
    
    def _get_least_loaded_user(self) -> int:
        """Get user with least workload."""
        if not MOCK_WORKLOAD:
            return 1
        return min(MOCK_WORKLOAD, key=MOCK_WORKLOAD.get)
    
    async def create_event_task(
        self,
        case_id: int,
        title: str,
        description: str,
        trigger: TriggerType,
        priority: TaskPriority = TaskPriority.MEDIUM,
        deadline_days: int = 3
    ) -> AgentTask:
        """
        Create a task triggered by an event.
        
        Args:
            case_id: Case ID
            title: Task title
            description: Task description
            trigger: What triggered this task
            priority: Task priority
            deadline_days: Days until deadline
            
        Returns:
            Created task
        """
        task = AgentTask(
            task_id=self._generate_task_id(case_id),
            case_id=case_id,
            title=title,
            description=description,
            priority=priority,
            status=TaskStatus.PENDING,
            trigger=trigger,
            created_at=datetime.utcnow(),
            deadline=datetime.utcnow() + timedelta(days=deadline_days)
        )
        
        # Auto-assign
        task.assigned_to = self._get_least_loaded_user()
        task.assigned_at = datetime.utcnow()
        task.status = TaskStatus.ASSIGNED
        
        self.tasks[task.task_id] = task
        await self._send_notification(task, "created")
        
        return task
    
    async def complete_task(self, task_id: str) -> Optional[AgentTask]:
        """Mark a task as completed."""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        
        # Update workload
        if task.assigned_to:
            MOCK_WORKLOAD[task.assigned_to] = max(0, MOCK_WORKLOAD.get(task.assigned_to, 1) - 1)
        
        await self._send_notification(task, "completed")
        return task
    
    async def check_overdue_tasks(self) -> List[AgentTask]:
        """Check and mark overdue tasks."""
        overdue = []
        now = datetime.utcnow()
        
        for task in self.tasks.values():
            if task.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
                if task.deadline < now:
                    task.status = TaskStatus.OVERDUE
                    overdue.append(task)
                    await self._send_notification(task, "overdue")
        
        return overdue
    
    async def _send_notification(self, task: AgentTask, event: str):
        """
        Send notification for task event.
        
        For demo: console.log
        Production: Twilio SMS/WhatsApp
        """
        notification = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "task_id": task.task_id,
            "case_id": task.case_id,
            "title": task.title,
            "assigned_to": task.assigned_to,
            "priority": task.priority.value,
            "message": self._get_notification_message(task, event)
        }
        
        self.notifications.append(notification)
        
        # Console log for demo
        print(f"📢 NOTIFICATION [{event.upper()}]: {notification['message']}")
    
    def _get_notification_message(self, task: AgentTask, event: str) -> str:
        """Generate notification message."""
        if event == "created":
            return f"New task '{task.title}' created for Case #{task.case_id}. Deadline: {task.deadline.strftime('%Y-%m-%d')}"
        elif event == "completed":
            return f"Task '{task.title}' for Case #{task.case_id} has been completed."
        elif event == "overdue":
            return f"⚠️ OVERDUE: Task '{task.title}' for Case #{task.case_id} is past deadline!"
        else:
            return f"Task update: {task.title}"
    
    def get_case_tasks(self, case_id: int) -> List[Dict[str, Any]]:
        """Get all tasks for a case."""
        return [t.to_dict() for t in self.tasks.values() if t.case_id == case_id]
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get all pending tasks."""
        return [t.to_dict() for t in self.tasks.values() 
                if t.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED]]
    
    def get_notifications(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent notifications."""
        return self.notifications[-limit:]


# Singleton instance
_agent: Optional[TaskAutomationAgent] = None


def get_task_agent() -> TaskAutomationAgent:
    """Get or create the task agent instance."""
    global _agent
    if _agent is None:
        _agent = TaskAutomationAgent()
    return _agent
