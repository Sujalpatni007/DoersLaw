"""
DOER Platform - Timeline Generator Agent

Rule-based timeline generation with templates for different dispute types.

FEATURES:
- Templates per dispute type
- Complexity-based duration adjustments
- Milestone tracking
- Dynamic deadline calculation

PRODUCTION UPGRADES:
- ML-based duration prediction
- Integration with court calendars
- Holiday/weekend handling
- SLA monitoring
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum


class MilestoneStatus(str, Enum):
    """Milestone status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    SKIPPED = "skipped"


@dataclass
class Milestone:
    """A timeline milestone."""
    name: str
    description: str
    phase: str
    duration_days: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: MilestoneStatus = MilestoneStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "phase": self.phase,
            "duration_days": self.duration_days,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "metadata": self.metadata
        }


# Timeline templates by dispute type
TIMELINE_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "ownership_dispute": [
        {"name": "Document Collection", "phase": "intake", "days": 7, "desc": "Gather ownership documents"},
        {"name": "Title Verification", "phase": "verification", "days": 5, "desc": "Verify title deeds"},
        {"name": "Ownership Analysis", "phase": "analysis", "days": 7, "desc": "Analyze ownership claims"},
        {"name": "Party Notification", "phase": "negotiation", "days": 3, "desc": "Notify all parties"},
        {"name": "Mediation Sessions", "phase": "negotiation", "days": 21, "desc": "Conduct mediation"},
        {"name": "Agreement Drafting", "phase": "resolution", "days": 7, "desc": "Draft settlement"},
        {"name": "Final Sign-off", "phase": "closure", "days": 5, "desc": "Complete signatures"},
    ],
    "boundary_dispute": [
        {"name": "Survey Request", "phase": "intake", "days": 5, "desc": "Request land survey"},
        {"name": "Survey Execution", "phase": "verification", "days": 14, "desc": "Complete survey"},
        {"name": "Boundary Analysis", "phase": "analysis", "days": 7, "desc": "Analyze survey results"},
        {"name": "Neighbor Consultation", "phase": "negotiation", "days": 14, "desc": "Consult with neighbors"},
        {"name": "Boundary Agreement", "phase": "resolution", "days": 7, "desc": "Draft boundary agreement"},
        {"name": "Registration", "phase": "closure", "days": 7, "desc": "Register new boundaries"},
    ],
    "inheritance_dispute": [
        {"name": "Heir Identification", "phase": "intake", "days": 7, "desc": "Identify all legal heirs"},
        {"name": "Will Verification", "phase": "verification", "days": 10, "desc": "Locate and verify will"},
        {"name": "Asset Valuation", "phase": "analysis", "days": 14, "desc": "Value inheritance"},
        {"name": "Heir Negotiation", "phase": "negotiation", "days": 30, "desc": "Negotiate partition"},
        {"name": "Partition Deed", "phase": "resolution", "days": 14, "desc": "Draft partition deed"},
        {"name": "Mutation Entry", "phase": "closure", "days": 21, "desc": "Update land records"},
    ],
    "encroachment": [
        {"name": "Evidence Collection", "phase": "intake", "days": 5, "desc": "Collect encroachment proof"},
        {"name": "Site Inspection", "phase": "verification", "days": 7, "desc": "Physical verification"},
        {"name": "Extent Analysis", "phase": "analysis", "days": 5, "desc": "Measure encroachment"},
        {"name": "Mediation Window", "phase": "negotiation", "days": 14, "desc": "Attempt amicable resolution"},
        {"name": "Notice Period", "phase": "negotiation", "days": 30, "desc": "Legal notice period"},
        {"name": "Eviction/Settlement", "phase": "resolution", "days": 14, "desc": "Execute resolution"},
        {"name": "Restoration", "phase": "closure", "days": 7, "desc": "Restore boundaries"},
    ],
    "title_issue": [
        {"name": "Title Search", "phase": "intake", "days": 7, "desc": "Search title history"},
        {"name": "Chain Verification", "phase": "verification", "days": 14, "desc": "Verify ownership chain"},
        {"name": "Defect Analysis", "phase": "analysis", "days": 10, "desc": "Identify title defects"},
        {"name": "Stakeholder Meeting", "phase": "negotiation", "days": 7, "desc": "Meet with parties"},
        {"name": "Title Rectification", "phase": "resolution", "days": 21, "desc": "Correct title issues"},
        {"name": "Registration Update", "phase": "closure", "days": 14, "desc": "Update registry"},
    ],
}

# Complexity multipliers
COMPLEXITY_MULTIPLIERS = {
    "low": 0.8,
    "medium": 1.0,
    "high": 1.5,
    "very_high": 2.0
}

# Location-based adjustments (days to add)
LOCATION_ADJUSTMENTS = {
    "rural": 7,  # Rural areas may have slower processes
    "urban": 0,
    "remote": 14,
    "metropolitan": -3  # Faster in major cities
}


class TimelineGeneratorAgent:
    """
    Generate dynamic timelines for dispute cases.
    
    Rule-based with templates - no LLM required for speed.
    """
    
    def __init__(self):
        """Initialize the timeline generator."""
        self.templates = TIMELINE_TEMPLATES
    
    def calculate_complexity_score(
        self,
        dispute_type: str,
        num_parties: int = 2,
        num_documents: int = 1,
        has_legal_issues: bool = False,
        value_crores: float = 0.0
    ) -> tuple:
        """
        Calculate complexity score and level.
        
        Returns:
            Tuple of (complexity_level, score)
        """
        score = 0
        
        # Base complexity by type
        type_scores = {
            "ownership_dispute": 3,
            "inheritance_dispute": 4,
            "boundary_dispute": 2,
            "encroachment": 2,
            "title_issue": 3
        }
        score += type_scores.get(dispute_type, 2)
        
        # Party complexity
        if num_parties > 4:
            score += 3
        elif num_parties > 2:
            score += 1
        
        # Document complexity
        if num_documents > 10:
            score += 2
        elif num_documents > 5:
            score += 1
        
        # Legal issues
        if has_legal_issues:
            score += 2
        
        # Value-based complexity
        if value_crores > 10:
            score += 3
        elif value_crores > 1:
            score += 1
        
        # Determine level
        if score <= 3:
            level = "low"
        elif score <= 6:
            level = "medium"
        elif score <= 9:
            level = "high"
        else:
            level = "very_high"
        
        return level, score
    
    def generate_timeline(
        self,
        case_id: int,
        dispute_type: str,
        complexity: str = "medium",
        location_type: str = "urban",
        start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete timeline for a case.
        
        Args:
            case_id: Case ID
            dispute_type: Type of dispute
            complexity: Complexity level (low/medium/high/very_high)
            location_type: Location type for adjustments
            start_date: Timeline start date (defaults to now)
            
        Returns:
            Timeline with milestones and metadata
        """
        if start_date is None:
            start_date = datetime.utcnow()
        
        # Get template
        template = self.templates.get(dispute_type, self.templates["ownership_dispute"])
        
        # Get multipliers
        multiplier = COMPLEXITY_MULTIPLIERS.get(complexity, 1.0)
        location_days = LOCATION_ADJUSTMENTS.get(location_type, 0)
        
        # Generate milestones
        milestones = []
        current_date = start_date
        
        for item in template:
            # Calculate adjusted duration
            base_days = item["days"]
            adjusted_days = int(base_days * multiplier)
            
            # Add location adjustment to first milestone only
            if len(milestones) == 0:
                adjusted_days += location_days
            
            adjusted_days = max(1, adjusted_days)  # Minimum 1 day
            
            milestone = Milestone(
                name=item["name"],
                description=item["desc"],
                phase=item["phase"],
                duration_days=adjusted_days,
                start_date=current_date,
                end_date=current_date + timedelta(days=adjusted_days),
                status=MilestoneStatus.PENDING
            )
            
            milestones.append(milestone)
            current_date = milestone.end_date
        
        # Mark first milestone as in progress
        if milestones:
            milestones[0].status = MilestoneStatus.IN_PROGRESS
        
        # Calculate totals
        total_days = sum(m.duration_days for m in milestones)
        expected_completion = start_date + timedelta(days=total_days)
        
        return {
            "case_id": case_id,
            "dispute_type": dispute_type,
            "complexity": complexity,
            "location_type": location_type,
            "generated_at": datetime.utcnow().isoformat(),
            "start_date": start_date.isoformat(),
            "expected_completion": expected_completion.isoformat(),
            "total_days": total_days,
            "milestone_count": len(milestones),
            "milestones": [m.to_dict() for m in milestones],
            "phase_summary": self._get_phase_summary(milestones)
        }
    
    def _get_phase_summary(self, milestones: List[Milestone]) -> Dict[str, int]:
        """Get duration summary by phase."""
        summary = {}
        for m in milestones:
            if m.phase not in summary:
                summary[m.phase] = 0
            summary[m.phase] += m.duration_days
        return summary
    
    def update_milestone_status(
        self,
        timeline: Dict[str, Any],
        milestone_name: str,
        new_status: MilestoneStatus
    ) -> Dict[str, Any]:
        """Update the status of a milestone."""
        for milestone in timeline["milestones"]:
            if milestone["name"] == milestone_name:
                milestone["status"] = new_status.value
                
                # If completed, mark next as in_progress
                if new_status == MilestoneStatus.COMPLETED:
                    idx = timeline["milestones"].index(milestone)
                    if idx + 1 < len(timeline["milestones"]):
                        timeline["milestones"][idx + 1]["status"] = MilestoneStatus.IN_PROGRESS.value
                
                break
        
        return timeline


# Singleton instance
_agent: Optional[TimelineGeneratorAgent] = None


def get_timeline_agent() -> TimelineGeneratorAgent:
    """Get or create the timeline agent instance."""
    global _agent
    if _agent is None:
        _agent = TimelineGeneratorAgent()
    return _agent
