"""
DOER Platform - Legal Talent Marketplace Service

Manages legal professionals (lawyers, para-legals, mediators) with matching algorithm.

MATCHING ALGORITHM:
1. Filter: Location + Specialization + Availability
2. Score = (success_rate * 0.4) + (speed_score * 0.3) + (workload_penalty * 0.3)
3. Return top 3

SPECIALIZATIONS:
- land_law, civil_law, mediation, revenue_law, property_law

PRODUCTION UPGRADES:
- Integration with bar council verification API
- Client feedback and rating system
- Geographic proximity scoring with coordinates
- Machine learning-based matching
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import random


class Specialization(str, Enum):
    """Legal specializations."""
    LAND_LAW = "land_law"
    CIVIL_LAW = "civil_law"
    MEDIATION = "mediation"
    REVENUE_LAW = "revenue_law"
    PROPERTY_LAW = "property_law"


class TalentType(str, Enum):
    """Types of legal talent."""
    LAWYER = "lawyer"
    PARALEGAL = "paralegal"
    MEDIATOR = "mediator"


class VerificationStatus(str, Enum):
    """Verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class AvailabilityStatus(str, Enum):
    """Availability for new cases."""
    AVAILABLE = "available"
    BUSY = "busy"
    ON_LEAVE = "on_leave"


@dataclass
class LegalTalent:
    """Legal professional profile."""
    talent_id: int
    name: str
    talent_type: TalentType
    specializations: List[Specialization]
    state: str
    district: str
    bar_council_id: Optional[str] = None
    email: str = ""
    phone: str = ""
    years_experience: int = 0
    bio: str = ""
    
    # Performance metrics
    cases_handled: int = 0
    cases_won: int = 0
    success_rate: float = 0.0
    avg_resolution_days: float = 30.0
    active_cases: int = 0
    max_cases: int = 10
    
    # Status
    verification_status: VerificationStatus = VerificationStatus.VERIFIED
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE
    
    # Metadata
    profile_photo: Optional[str] = None
    languages: List[str] = field(default_factory=lambda: ["English", "Hindi"])
    hourly_rate: float = 500.0  # INR
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "talent_id": self.talent_id,
            "name": self.name,
            "talent_type": self.talent_type.value,
            "specializations": [s.value for s in self.specializations],
            "state": self.state,
            "district": self.district,
            "bar_council_id": self.bar_council_id,
            "email": self.email,
            "phone": self.phone,
            "years_experience": self.years_experience,
            "bio": self.bio,
            "cases_handled": self.cases_handled,
            "cases_won": self.cases_won,
            "success_rate": self.success_rate,
            "avg_resolution_days": self.avg_resolution_days,
            "active_cases": self.active_cases,
            "max_cases": self.max_cases,
            "verification_status": self.verification_status.value,
            "availability": self.availability.value,
            "languages": self.languages,
            "hourly_rate": self.hourly_rate,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class CaseAssignment:
    """Case assignment to legal talent."""
    assignment_id: str
    case_id: int
    talent_id: int
    assigned_at: datetime
    role: str  # lead_counsel, co_counsel, mediator
    status: str = "active"  # active, completed, withdrawn
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "case_id": self.case_id,
            "talent_id": self.talent_id,
            "assigned_at": self.assigned_at.isoformat(),
            "role": self.role,
            "status": self.status,
            "notes": self.notes
        }


# Seed data: 10 lawyers across Maharashtra, UP, Karnataka
SEED_TALENT: List[Dict[str, Any]] = [
    # Maharashtra
    {
        "talent_id": 1,
        "name": "Adv. Rajesh Kulkarni",
        "talent_type": TalentType.LAWYER,
        "specializations": [Specialization.LAND_LAW, Specialization.PROPERTY_LAW],
        "state": "Maharashtra",
        "district": "Pune",
        "bar_council_id": "MH/2015/12345",
        "email": "rajesh.kulkarni@legal.com",
        "phone": "+91-9876543210",
        "years_experience": 12,
        "bio": "Senior land law expert with 12 years experience in property disputes",
        "cases_handled": 145,
        "cases_won": 112,
        "success_rate": 0.77,
        "avg_resolution_days": 45,
        "active_cases": 5,
        "languages": ["English", "Hindi", "Marathi"],
        "hourly_rate": 2500.0
    },
    {
        "talent_id": 2,
        "name": "Adv. Priya Deshmukh",
        "talent_type": TalentType.LAWYER,
        "specializations": [Specialization.CIVIL_LAW, Specialization.LAND_LAW],
        "state": "Maharashtra",
        "district": "Mumbai",
        "bar_council_id": "MH/2010/54321",
        "email": "priya.deshmukh@legal.com",
        "phone": "+91-9876543211",
        "years_experience": 15,
        "bio": "High court advocate specializing in civil and land disputes",
        "cases_handled": 210,
        "cases_won": 178,
        "success_rate": 0.85,
        "avg_resolution_days": 38,
        "active_cases": 7,
        "languages": ["English", "Hindi", "Marathi"],
        "hourly_rate": 4000.0
    },
    {
        "talent_id": 3,
        "name": "Shri Vinod Patil",
        "talent_type": TalentType.MEDIATOR,
        "specializations": [Specialization.MEDIATION],
        "state": "Maharashtra",
        "district": "Nagpur",
        "bar_council_id": None,
        "email": "vinod.patil@mediate.com",
        "phone": "+91-9876543212",
        "years_experience": 20,
        "bio": "Certified mediator with expertise in land dispute resolution",
        "cases_handled": 320,
        "cases_won": 288,
        "success_rate": 0.90,
        "avg_resolution_days": 21,
        "active_cases": 3,
        "languages": ["English", "Hindi", "Marathi"],
        "hourly_rate": 1500.0
    },
    # Uttar Pradesh
    {
        "talent_id": 4,
        "name": "Adv. Arun Kumar Sharma",
        "talent_type": TalentType.LAWYER,
        "specializations": [Specialization.REVENUE_LAW, Specialization.LAND_LAW],
        "state": "Uttar Pradesh",
        "district": "Lucknow",
        "bar_council_id": "UP/2008/11111",
        "email": "arun.sharma@legal.com",
        "phone": "+91-9876543213",
        "years_experience": 18,
        "bio": "Revenue law specialist with extensive experience in UP courts",
        "cases_handled": 280,
        "cases_won": 224,
        "success_rate": 0.80,
        "avg_resolution_days": 52,
        "active_cases": 8,
        "languages": ["English", "Hindi"],
        "hourly_rate": 2000.0
    },
    {
        "talent_id": 5,
        "name": "Adv. Sunita Yadav",
        "talent_type": TalentType.LAWYER,
        "specializations": [Specialization.PROPERTY_LAW, Specialization.CIVIL_LAW],
        "state": "Uttar Pradesh",
        "district": "Varanasi",
        "bar_council_id": "UP/2012/22222",
        "email": "sunita.yadav@legal.com",
        "phone": "+91-9876543214",
        "years_experience": 10,
        "bio": "Property law expert handling inheritance and partition cases",
        "cases_handled": 95,
        "cases_won": 72,
        "success_rate": 0.76,
        "avg_resolution_days": 48,
        "active_cases": 4,
        "languages": ["English", "Hindi"],
        "hourly_rate": 1800.0
    },
    {
        "talent_id": 6,
        "name": "Ms. Rekha Gupta",
        "talent_type": TalentType.PARALEGAL,
        "specializations": [Specialization.LAND_LAW, Specialization.REVENUE_LAW],
        "state": "Uttar Pradesh",
        "district": "Agra",
        "bar_council_id": None,
        "email": "rekha.gupta@paralegal.com",
        "phone": "+91-9876543215",
        "years_experience": 8,
        "bio": "Experienced paralegal for document preparation and filing",
        "cases_handled": 180,
        "cases_won": 162,
        "success_rate": 0.90,
        "avg_resolution_days": 30,
        "active_cases": 6,
        "languages": ["English", "Hindi"],
        "hourly_rate": 800.0
    },
    # Karnataka
    {
        "talent_id": 7,
        "name": "Adv. Suresh Rao",
        "talent_type": TalentType.LAWYER,
        "specializations": [Specialization.LAND_LAW, Specialization.CIVIL_LAW],
        "state": "Karnataka",
        "district": "Bangalore",
        "bar_council_id": "KA/2009/33333",
        "email": "suresh.rao@legal.com",
        "phone": "+91-9876543216",
        "years_experience": 16,
        "bio": "Senior advocate at Karnataka High Court for land matters",
        "cases_handled": 198,
        "cases_won": 163,
        "success_rate": 0.82,
        "avg_resolution_days": 42,
        "active_cases": 6,
        "languages": ["English", "Hindi", "Kannada"],
        "hourly_rate": 3500.0
    },
    {
        "talent_id": 8,
        "name": "Adv. Lakshmi Narayana",
        "talent_type": TalentType.LAWYER,
        "specializations": [Specialization.PROPERTY_LAW, Specialization.MEDIATION],
        "state": "Karnataka",
        "district": "Mysore",
        "bar_council_id": "KA/2014/44444",
        "email": "lakshmi.n@legal.com",
        "phone": "+91-9876543217",
        "years_experience": 9,
        "bio": "Property law advocate with mediation certification",
        "cases_handled": 78,
        "cases_won": 65,
        "success_rate": 0.83,
        "avg_resolution_days": 35,
        "active_cases": 3,
        "languages": ["English", "Hindi", "Kannada", "Tamil"],
        "hourly_rate": 2200.0
    },
    {
        "talent_id": 9,
        "name": "Shri Manjunath",
        "talent_type": TalentType.MEDIATOR,
        "specializations": [Specialization.MEDIATION],
        "state": "Karnataka",
        "district": "Hubli-Dharwad",
        "bar_council_id": None,
        "email": "manjunath@mediate.com",
        "phone": "+91-9876543218",
        "years_experience": 22,
        "bio": "Government-empaneled mediator for land disputes",
        "cases_handled": 450,
        "cases_won": 423,
        "success_rate": 0.94,
        "avg_resolution_days": 18,
        "active_cases": 2,
        "languages": ["English", "Hindi", "Kannada"],
        "hourly_rate": 1200.0
    },
    {
        "talent_id": 10,
        "name": "Adv. Deepak Hegde",
        "talent_type": TalentType.LAWYER,
        "specializations": [Specialization.REVENUE_LAW, Specialization.LAND_LAW, Specialization.CIVIL_LAW],
        "state": "Karnataka",
        "district": "Bangalore",
        "bar_council_id": "KA/2006/55555",
        "email": "deepak.hegde@legal.com",
        "phone": "+91-9876543219",
        "years_experience": 20,
        "bio": "Senior counsel with multi-domain expertise in land matters",
        "cases_handled": 340,
        "cases_won": 289,
        "success_rate": 0.85,
        "avg_resolution_days": 40,
        "active_cases": 9,
        "languages": ["English", "Hindi", "Kannada"],
        "hourly_rate": 5000.0
    },
]


class TalentMarketplaceService:
    """
    Service for managing legal talent marketplace.
    """
    
    def __init__(self):
        """Initialize with seed data."""
        self.talent: Dict[int, LegalTalent] = {}
        self.assignments: Dict[str, CaseAssignment] = {}
        self.assignment_counter = 0
        
        self._load_seed_data()
    
    def _load_seed_data(self):
        """Load seed talent data."""
        for data in SEED_TALENT:
            talent = LegalTalent(
                talent_id=data["talent_id"],
                name=data["name"],
                talent_type=data["talent_type"],
                specializations=data["specializations"],
                state=data["state"],
                district=data["district"],
                bar_council_id=data.get("bar_council_id"),
                email=data.get("email", ""),
                phone=data.get("phone", ""),
                years_experience=data.get("years_experience", 0),
                bio=data.get("bio", ""),
                cases_handled=data.get("cases_handled", 0),
                cases_won=data.get("cases_won", 0),
                success_rate=data.get("success_rate", 0.0),
                avg_resolution_days=data.get("avg_resolution_days", 30.0),
                active_cases=data.get("active_cases", 0),
                languages=data.get("languages", ["English", "Hindi"]),
                hourly_rate=data.get("hourly_rate", 500.0)
            )
            self.talent[talent.talent_id] = talent
        
        print(f"✅ Loaded {len(self.talent)} legal professionals")
    
    def get_all_talent(self) -> List[Dict[str, Any]]:
        """Get all talent profiles."""
        return [t.to_dict() for t in self.talent.values()]
    
    def get_talent(self, talent_id: int) -> Optional[Dict[str, Any]]:
        """Get single talent profile."""
        talent = self.talent.get(talent_id)
        return talent.to_dict() if talent else None
    
    def search_talent(
        self,
        state: Optional[str] = None,
        district: Optional[str] = None,
        specialization: Optional[str] = None,
        talent_type: Optional[str] = None,
        available_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Search talent with filters."""
        results = []
        
        for talent in self.talent.values():
            # Filter by availability
            if available_only and talent.availability != AvailabilityStatus.AVAILABLE:
                continue
            
            # Filter by state
            if state and talent.state.lower() != state.lower():
                continue
            
            # Filter by district
            if district and talent.district.lower() != district.lower():
                continue
            
            # Filter by specialization
            if specialization:
                spec_values = [s.value for s in talent.specializations]
                if specialization.lower() not in [s.lower() for s in spec_values]:
                    continue
            
            # Filter by type
            if talent_type and talent.talent_type.value.lower() != talent_type.lower():
                continue
            
            results.append(talent.to_dict())
        
        return results
    
    def match_talent(
        self,
        case_id: int,
        state: str,
        district: str,
        dispute_type: str,
        complexity: str = "medium",
        top_n: int = 3
    ) -> Dict[str, Any]:
        """
        Match talent to case using scoring algorithm.
        
        Score = (success_rate * 0.4) + (speed_score * 0.3) + (workload_penalty * 0.3)
        
        Args:
            case_id: Case ID
            state: Case state
            district: Case district
            dispute_type: Type of dispute
            complexity: Case complexity
            top_n: Number of matches to return
            
        Returns:
            Match results with scores
        """
        # Map dispute type to specialization
        type_to_spec = {
            "ownership_dispute": Specialization.LAND_LAW,
            "boundary_dispute": Specialization.LAND_LAW,
            "inheritance_dispute": Specialization.PROPERTY_LAW,
            "encroachment": Specialization.CIVIL_LAW,
            "title_issue": Specialization.REVENUE_LAW
        }
        target_spec = type_to_spec.get(dispute_type, Specialization.LAND_LAW)
        
        candidates = []
        
        for talent in self.talent.values():
            # Must be available and verified
            if talent.availability != AvailabilityStatus.AVAILABLE:
                continue
            if talent.verification_status != VerificationStatus.VERIFIED:
                continue
            
            # Location match (same state, prefer same district)
            if talent.state.lower() != state.lower():
                continue
            
            location_bonus = 0.1 if talent.district.lower() == district.lower() else 0
            
            # Specialization match
            has_spec = target_spec in talent.specializations
            if not has_spec:
                continue
            
            # Calculate scores
            # Success rate score (0-1)
            success_score = talent.success_rate
            
            # Speed score - normalize to 0-1 (lower days = higher score)
            max_days = 60.0
            speed_score = max(0, (max_days - talent.avg_resolution_days) / max_days)
            
            # Workload penalty - higher active cases = lower score
            workload_ratio = talent.active_cases / talent.max_cases
            workload_score = 1 - workload_ratio
            
            # Final score
            final_score = (
                (success_score * 0.4) +
                (speed_score * 0.3) +
                (workload_score * 0.3) +
                location_bonus
            )
            
            candidates.append({
                "talent": talent,
                "score": final_score,
                "breakdown": {
                    "success_score": round(success_score, 2),
                    "speed_score": round(speed_score, 2),
                    "workload_score": round(workload_score, 2),
                    "location_bonus": location_bonus,
                    "final_score": round(final_score, 3)
                }
            })
        
        # Sort by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top N
        matches = []
        for c in candidates[:top_n]:
            match = c["talent"].to_dict()
            match["match_score"] = c["breakdown"]
            matches.append(match)
        
        return {
            "case_id": case_id,
            "location": {"state": state, "district": district},
            "dispute_type": dispute_type,
            "target_specialization": target_spec.value,
            "matches_found": len(candidates),
            "top_matches": matches
        }
    
    def assign_talent(
        self,
        case_id: int,
        talent_id: int,
        role: str = "lead_counsel",
        notes: str = ""
    ) -> Optional[CaseAssignment]:
        """Assign talent to a case."""
        talent = self.talent.get(talent_id)
        if not talent:
            return None
        
        # Check availability
        if talent.active_cases >= talent.max_cases:
            return None
        
        self.assignment_counter += 1
        assignment = CaseAssignment(
            assignment_id=f"ASSIGN-{case_id}-{self.assignment_counter:04d}",
            case_id=case_id,
            talent_id=talent_id,
            assigned_at=datetime.utcnow(),
            role=role,
            notes=notes
        )
        
        # Update talent workload
        talent.active_cases += 1
        if talent.active_cases >= talent.max_cases:
            talent.availability = AvailabilityStatus.BUSY
        
        self.assignments[assignment.assignment_id] = assignment
        return assignment
    
    def get_case_assignments(self, case_id: int) -> List[Dict[str, Any]]:
        """Get all assignments for a case."""
        results = []
        for a in self.assignments.values():
            if a.case_id == case_id:
                data = a.to_dict()
                talent = self.talent.get(a.talent_id)
                if talent:
                    data["talent_name"] = talent.name
                    data["talent_type"] = talent.talent_type.value
                results.append(data)
        return results
    
    def complete_assignment(self, assignment_id: str, case_won: bool = True) -> Optional[CaseAssignment]:
        """Complete a case assignment."""
        assignment = self.assignments.get(assignment_id)
        if not assignment:
            return None
        
        assignment.status = "completed"
        
        # Update talent metrics
        talent = self.talent.get(assignment.talent_id)
        if talent:
            talent.active_cases = max(0, talent.active_cases - 1)
            talent.cases_handled += 1
            if case_won:
                talent.cases_won += 1
            talent.success_rate = talent.cases_won / talent.cases_handled
            talent.availability = AvailabilityStatus.AVAILABLE
        
        return assignment
    
    def get_talent_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics."""
        total = len(self.talent)
        lawyers = sum(1 for t in self.talent.values() if t.talent_type == TalentType.LAWYER)
        mediators = sum(1 for t in self.talent.values() if t.talent_type == TalentType.MEDIATOR)
        paralegals = sum(1 for t in self.talent.values() if t.talent_type == TalentType.PARALEGAL)
        available = sum(1 for t in self.talent.values() if t.availability == AvailabilityStatus.AVAILABLE)
        
        states = list(set(t.state for t in self.talent.values()))
        
        avg_success = sum(t.success_rate for t in self.talent.values()) / total if total > 0 else 0
        avg_resolution = sum(t.avg_resolution_days for t in self.talent.values()) / total if total > 0 else 0
        
        return {
            "total_talent": total,
            "lawyers": lawyers,
            "mediators": mediators,
            "paralegals": paralegals,
            "available": available,
            "states_covered": states,
            "avg_success_rate": round(avg_success, 2),
            "avg_resolution_days": round(avg_resolution, 1),
            "active_assignments": len([a for a in self.assignments.values() if a.status == "active"])
        }


# Singleton instance
_service: Optional[TalentMarketplaceService] = None


def get_talent_service() -> TalentMarketplaceService:
    """Get or create the talent marketplace service."""
    global _service
    if _service is None:
        _service = TalentMarketplaceService()
    return _service
