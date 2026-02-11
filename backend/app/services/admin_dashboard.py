"""
DOER Platform - Admin Dashboard Service

Admin functionality for case management and oversight.

FEATURES:
- View all active cases
- Reassign talent
- Override AI decisions
- Performance analytics

PRODUCTION UPGRADES:
- Role-based access control
- Audit logging
- Dashboard customization
- Export functionality
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import random


@dataclass
class AdminAction:
    """Records an admin action."""
    action_id: str
    admin_id: int
    action_type: str
    target_type: str
    target_id: str
    details: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "admin_id": self.admin_id,
            "action_type": self.action_type,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class AdminDashboardService:
    """
    Admin dashboard service for oversight and management.
    """
    
    def __init__(self):
        """Initialize the admin service."""
        self.actions: List[AdminAction] = []
        self.action_counter = 0
        
        # Mock case data for demo
        self._mock_cases = self._generate_mock_cases()
    
    def _generate_mock_cases(self) -> List[Dict[str, Any]]:
        """Generate mock case data for dashboard."""
        states = ["Maharashtra", "Uttar Pradesh", "Karnataka"]
        districts = {
            "Maharashtra": ["Pune", "Mumbai", "Nagpur"],
            "Uttar Pradesh": ["Lucknow", "Varanasi", "Agra"],
            "Karnataka": ["Bangalore", "Mysore", "Hubli-Dharwad"]
        }
        dispute_types = ["ownership_dispute", "boundary_dispute", "inheritance_dispute", "encroachment", "title_issue"]
        statuses = ["intake", "verification", "analysis", "negotiation", "resolution"]
        
        cases = []
        for i in range(1, 16):
            state = random.choice(states)
            district = random.choice(districts[state])
            created_days_ago = random.randint(1, 90)
            
            cases.append({
                "case_id": i,
                "title": f"Land Dispute Case #{i}",
                "dispute_type": random.choice(dispute_types),
                "state": state,
                "district": district,
                "status": random.choice(statuses),
                "priority": random.choice(["low", "medium", "high", "urgent"]),
                "created_at": (datetime.utcnow() - timedelta(days=created_days_ago)).isoformat(),
                "last_updated": (datetime.utcnow() - timedelta(days=random.randint(0, created_days_ago))).isoformat(),
                "assigned_talent": random.randint(1, 10) if random.random() > 0.2 else None,
                "documents_count": random.randint(0, 8),
                "completion_percentage": random.randint(10, 100)
            })
        
        return cases
    
    def get_all_cases(
        self,
        status: Optional[str] = None,
        state: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get all cases with filters."""
        cases = self._mock_cases.copy()
        
        # Apply filters
        if status:
            cases = [c for c in cases if c["status"] == status]
        if state:
            cases = [c for c in cases if c["state"].lower() == state.lower()]
        if priority:
            cases = [c for c in cases if c["priority"] == priority]
        
        total = len(cases)
        
        # Pagination
        cases = cases[offset:offset + limit]
        
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "cases": cases
        }
    
    def get_case_details(self, case_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed case info."""
        for case in self._mock_cases:
            if case["case_id"] == case_id:
                # Add more details
                details = case.copy()
                details["timeline_events"] = [
                    {"event": "Case Created", "date": case["created_at"]},
                    {"event": "Documents Uploaded", "date": case["last_updated"]},
                ]
                details["ai_decisions"] = [
                    {"type": "talent_match", "recommendation": "Adv. Rajesh Kulkarni", "confidence": 0.85},
                    {"type": "timeline", "recommendation": "45 days estimated", "confidence": 0.72}
                ]
                return details
        return None
    
    def reassign_talent(
        self,
        admin_id: int,
        case_id: int,
        old_talent_id: Optional[int],
        new_talent_id: int,
        reason: str
    ) -> Dict[str, Any]:
        """Reassign talent to a case."""
        self.action_counter += 1
        
        action = AdminAction(
            action_id=f"ADMIN-{self.action_counter:05d}",
            admin_id=admin_id,
            action_type="reassign_talent",
            target_type="case",
            target_id=str(case_id),
            details={
                "old_talent_id": old_talent_id,
                "new_talent_id": new_talent_id,
                "reason": reason
            },
            timestamp=datetime.utcnow()
        )
        self.actions.append(action)
        
        # Update mock case
        for case in self._mock_cases:
            if case["case_id"] == case_id:
                case["assigned_talent"] = new_talent_id
                case["last_updated"] = datetime.utcnow().isoformat()
                break
        
        return {
            "success": True,
            "action": action.to_dict(),
            "message": f"Case {case_id} reassigned from talent {old_talent_id} to {new_talent_id}"
        }
    
    def override_ai_decision(
        self,
        admin_id: int,
        case_id: int,
        decision_type: str,
        original_recommendation: str,
        override_value: str,
        reason: str
    ) -> Dict[str, Any]:
        """Override an AI decision."""
        self.action_counter += 1
        
        action = AdminAction(
            action_id=f"ADMIN-{self.action_counter:05d}",
            admin_id=admin_id,
            action_type="override_ai",
            target_type="decision",
            target_id=f"{case_id}-{decision_type}",
            details={
                "decision_type": decision_type,
                "original": original_recommendation,
                "override": override_value,
                "reason": reason
            },
            timestamp=datetime.utcnow()
        )
        self.actions.append(action)
        
        return {
            "success": True,
            "action": action.to_dict(),
            "message": f"AI {decision_type} decision overridden for case {case_id}"
        }
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get performance analytics dashboard data."""
        return {
            "summary": {
                "total_cases": 156,
                "active_cases": 45,
                "resolved_cases": 98,
                "pending_cases": 13,
                "avg_resolution_days": 38.5
            },
            "by_status": {
                "intake": 12,
                "verification": 8,
                "analysis": 10,
                "negotiation": 15,
                "resolution": 0,
                "closure": 98
            },
            "by_dispute_type": {
                "ownership_dispute": 45,
                "boundary_dispute": 32,
                "inheritance_dispute": 38,
                "encroachment": 28,
                "title_issue": 13
            },
            "by_state": {
                "Maharashtra": 52,
                "Uttar Pradesh": 48,
                "Karnataka": 56
            },
            "monthly_trends": {
                "cases_filed": [12, 15, 18, 22, 19, 14],
                "cases_resolved": [8, 12, 15, 18, 16, 12],
                "months": ["Aug", "Sep", "Oct", "Nov", "Dec", "Jan"]
            },
            "talent_performance": {
                "top_performers": [
                    {"talent_id": 9, "name": "Shri Manjunath", "success_rate": 0.94, "cases_closed": 45},
                    {"talent_id": 3, "name": "Shri Vinod Patil", "success_rate": 0.90, "cases_closed": 32},
                    {"talent_id": 2, "name": "Adv. Priya Deshmukh", "success_rate": 0.85, "cases_closed": 28}
                ],
                "avg_success_rate": 0.82,
                "avg_cases_per_talent": 15.6
            },
            "ai_metrics": {
                "matching_accuracy": 0.87,
                "timeline_accuracy": 0.72,
                "document_extraction_accuracy": 0.91,
                "total_ai_decisions": 450,
                "decisions_overridden": 23,
                "override_rate": 0.051
            }
        }
    
    def get_admin_actions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent admin actions."""
        return [a.to_dict() for a in self.actions[-limit:]]
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""
        return {
            "status": "healthy",
            "components": {
                "api": {"status": "up", "latency_ms": 45},
                "database": {"status": "up", "connections": 12},
                "scheduler": {"status": "up", "pending_jobs": 3},
                "websocket": {"status": "up", "active_connections": 8}
            },
            "uptime_hours": 168.5,
            "last_restart": (datetime.utcnow() - timedelta(hours=168)).isoformat(),
            "version": "1.0.0-beta"
        }


# Singleton instance
_service: Optional[AdminDashboardService] = None


def get_admin_service() -> AdminDashboardService:
    """Get or create the admin dashboard service."""
    global _service
    if _service is None:
        _service = AdminDashboardService()
    return _service
