"""
Analytics Service - Progress Transparency & Satisfaction Tracking
Generates demo data and calculates analytics
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from collections import Counter
import random
import uuid
import logging
import json

logger = logging.getLogger("ANALYTICS")


class CasePhase(str, Enum):
    INTAKE = "intake"
    VERIFICATION = "verification"
    ANALYSIS = "analysis"
    NEGOTIATION = "negotiation"
    RESOLUTION = "resolution"
    CLOSED = "closed"


@dataclass
class AnalyticsEvent:
    """Individual analytics event"""
    id: str
    event_type: str
    case_id: str
    user_id: int
    timestamp: datetime
    data: Dict
    

@dataclass
class SatisfactionSurvey:
    """Post-resolution satisfaction survey"""
    id: str
    case_id: str
    user_id: int
    rating: int  # 1-5
    would_recommend: bool  # For NPS
    feedback: str
    keywords: List[str]
    submitted_at: datetime


@dataclass
class CaseProgress:
    """Case progress timeline"""
    case_id: str
    current_phase: CasePhase
    phase_completion: Dict[str, float]  # Phase -> completion %
    started_at: datetime
    estimated_resolution: datetime
    similar_cases_avg_days: int
    milestones: List[Dict]


class AnalyticsService:
    """
    Analytics and transparency features
    """
    
    def __init__(self):
        self.events: List[AnalyticsEvent] = []
        self.surveys: Dict[str, SatisfactionSurvey] = {}
        self.demo_cases: List[Dict] = []
        self.demo_mode = False
        
        # Phase weights for progress calculation
        self.phase_weights = {
            CasePhase.INTAKE: 0.10,
            CasePhase.VERIFICATION: 0.20,
            CasePhase.ANALYSIS: 0.25,
            CasePhase.NEGOTIATION: 0.25,
            CasePhase.RESOLUTION: 0.15,
            CasePhase.CLOSED: 0.05,
        }
        
        # Average resolution times by case type (days)
        self.avg_resolution_days = {
            "boundary_dispute": 45,
            "ownership_dispute": 60,
            "encroachment": 35,
            "inheritance": 50,
            "mutation": 25,
            "general": 40,
        }
    
    def generate_demo_data(self, months: int = 3) -> Dict:
        """Generate 3 months of realistic historical data"""
        self.demo_mode = True
        self.demo_cases = []
        self.events = []
        self.surveys = {}
        
        states = ["Maharashtra", "UP", "Karnataka", "Tamil Nadu", "Gujarat", "Rajasthan"]
        districts = {
            "Maharashtra": ["Pune", "Mumbai", "Nashik", "Nagpur"],
            "UP": ["Varanasi", "Lucknow", "Agra", "Kanpur"],
            "Karnataka": ["Bangalore", "Mysore", "Hubli"],
            "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
            "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
            "Rajasthan": ["Jaipur", "Udaipur", "Jodhpur"],
        }
        case_types = ["boundary_dispute", "ownership_dispute", "encroachment", "inheritance", "mutation"]
        
        start_date = datetime.now() - timedelta(days=months * 30)
        cases_count = months * 50  # ~50 cases per month
        
        for i in range(cases_count):
            state = random.choice(states)
            district = random.choice(districts[state])
            case_type = random.choice(case_types)
            
            # Random start within the period
            days_offset = random.randint(0, months * 30)
            case_start = start_date + timedelta(days=days_offset)
            
            # Determine current phase based on age
            age_days = (datetime.now() - case_start).days
            if age_days < 5:
                phase = CasePhase.INTAKE
            elif age_days < 15:
                phase = CasePhase.VERIFICATION
            elif age_days < 30:
                phase = CasePhase.ANALYSIS
            elif age_days < 45:
                phase = CasePhase.NEGOTIATION
            elif age_days < 60:
                phase = CasePhase.RESOLUTION
            else:
                phase = CasePhase.CLOSED
            
            # Resolution method
            resolved_by = random.choice(["ai", "human", "human"]) if phase == CasePhase.CLOSED else None
            
            case = {
                "id": f"CASE-{(start_date + timedelta(days=days_offset)).year}-{10000 + i:05d}",
                "type": case_type,
                "state": state,
                "district": district,
                "phase": phase.value,
                "started_at": case_start.isoformat(),
                "resolved_at": (case_start + timedelta(days=random.randint(30, 70))).isoformat() if phase == CasePhase.CLOSED else None,
                "resolved_by": resolved_by,
                "user_id": random.randint(1, 100),
                "talent_id": random.randint(1, 20),
            }
            self.demo_cases.append(case)
            
            # Generate satisfaction survey for closed cases
            if phase == CasePhase.CLOSED:
                rating = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 15, 35, 35])[0]
                survey = SatisfactionSurvey(
                    id=str(uuid.uuid4()),
                    case_id=case["id"],
                    user_id=case["user_id"],
                    rating=rating,
                    would_recommend=rating >= 4,
                    feedback=self._generate_feedback(rating),
                    keywords=self._extract_keywords(rating),
                    submitted_at=datetime.fromisoformat(case["resolved_at"]) + timedelta(days=random.randint(1, 5)),
                )
                self.surveys[survey.id] = survey
        
        # Generate analytics events
        for case in self.demo_cases:
            for event_type in ["case_created", "phase_changed", "document_uploaded", "message_sent"]:
                self.events.append(AnalyticsEvent(
                    id=str(uuid.uuid4()),
                    event_type=event_type,
                    case_id=case["id"],
                    user_id=case["user_id"],
                    timestamp=datetime.fromisoformat(case["started_at"]) + timedelta(days=random.randint(0, 30)),
                    data={"phase": case["phase"]},
                ))
        
        logger.info(f"Generated {len(self.demo_cases)} demo cases, {len(self.surveys)} surveys, {len(self.events)} events")
        
        return {
            "demo_mode": True,
            "cases_generated": len(self.demo_cases),
            "surveys_generated": len(self.surveys),
            "events_generated": len(self.events),
            "period": f"{months} months",
        }
    
    def _generate_feedback(self, rating: int) -> str:
        positive = ["Excellent service!", "Very helpful lawyers", "Quick resolution", "Professional team", "Easy to use platform"]
        neutral = ["Service was okay", "Could be faster", "Average experience", "Decent support"]
        negative = ["Too slow", "Poor communication", "Not satisfied", "Expected better service"]
        
        if rating >= 4:
            return random.choice(positive)
        elif rating == 3:
            return random.choice(neutral)
        else:
            return random.choice(negative)
    
    def _extract_keywords(self, rating: int) -> List[str]:
        positive = ["excellent", "helpful", "quick", "professional", "easy"]
        neutral = ["okay", "average", "decent"]
        negative = ["slow", "poor", "unsatisfied", "disappointing"]
        
        if rating >= 4:
            return random.sample(positive, min(2, len(positive)))
        elif rating == 3:
            return random.sample(neutral, min(2, len(neutral)))
        else:
            return random.sample(negative, min(2, len(negative)))
    
    # =========================================================================
    # Progress Transparency
    # =========================================================================
    
    def get_case_progress(self, case_id: str) -> CaseProgress:
        """Get visual case timeline with completion percentages"""
        # Find case in demo data or mock
        case = next((c for c in self.demo_cases if c["id"] == case_id), None)
        
        if not case:
            # Create mock for demo
            case = {
                "id": case_id,
                "type": "boundary_dispute",
                "started_at": (datetime.now() - timedelta(days=random.randint(10, 40))).isoformat(),
                "phase": random.choice([p.value for p in CasePhase]),
            }
        
        current_phase = CasePhase(case["phase"])
        started_at = datetime.fromisoformat(case["started_at"])
        
        # Calculate phase completions
        phases = list(CasePhase)
        current_idx = phases.index(current_phase)
        
        phase_completion = {}
        for i, phase in enumerate(phases):
            if i < current_idx:
                phase_completion[phase.value] = 100
            elif i == current_idx:
                phase_completion[phase.value] = random.randint(30, 80)
            else:
                phase_completion[phase.value] = 0
        
        # Calculate estimated resolution
        case_type = case.get("type", "general")
        avg_days = self.avg_resolution_days.get(case_type, 40)
        age = (datetime.now() - started_at).days
        remaining = max(10, avg_days - age)
        estimated_resolution = datetime.now() + timedelta(days=remaining)
        
        # Generate milestones
        milestones = [
            {"phase": "intake", "title": "Case Registered", "date": started_at.isoformat(), "completed": True},
            {"phase": "verification", "title": "Documents Verified", "date": (started_at + timedelta(days=7)).isoformat(), "completed": current_idx >= 1},
            {"phase": "analysis", "title": "Legal Analysis Done", "date": (started_at + timedelta(days=20)).isoformat(), "completed": current_idx >= 2},
            {"phase": "negotiation", "title": "Settlement Negotiation", "date": (started_at + timedelta(days=35)).isoformat(), "completed": current_idx >= 3},
            {"phase": "resolution", "title": "Final Resolution", "date": estimated_resolution.isoformat(), "completed": current_idx >= 4},
        ]
        
        return CaseProgress(
            case_id=case_id,
            current_phase=current_phase,
            phase_completion=phase_completion,
            started_at=started_at,
            estimated_resolution=estimated_resolution,
            similar_cases_avg_days=avg_days,
            milestones=milestones,
        )
    
    def get_similar_cases_stats(self, case_type: str, state: str = None) -> Dict:
        """Get statistics for similar cases"""
        similar = [c for c in self.demo_cases if c["type"] == case_type]
        if state:
            similar = [c for c in similar if c["state"] == state]
        
        resolved = [c for c in similar if c["phase"] == "closed"]
        
        if not resolved:
            return {
                "similar_count": len(similar),
                "resolved_count": 0,
                "avg_resolution_days": self.avg_resolution_days.get(case_type, 40),
                "success_rate": 0.85,
            }
        
        # Calculate avg resolution time
        resolution_times = []
        for c in resolved:
            start = datetime.fromisoformat(c["started_at"])
            end = datetime.fromisoformat(c["resolved_at"])
            resolution_times.append((end - start).days)
        
        return {
            "similar_count": len(similar),
            "resolved_count": len(resolved),
            "avg_resolution_days": sum(resolution_times) // len(resolution_times) if resolution_times else 40,
            "min_days": min(resolution_times) if resolution_times else 20,
            "max_days": max(resolution_times) if resolution_times else 60,
            "success_rate": 0.87,
        }
    
    # =========================================================================
    # Satisfaction Tracking
    # =========================================================================
    
    def submit_survey(self, case_id: str, user_id: int, rating: int, would_recommend: bool, feedback: str) -> SatisfactionSurvey:
        """Submit post-resolution satisfaction survey"""
        keywords = []
        feedback_lower = feedback.lower()
        keyword_map = {
            "excellent": ["excellent", "amazing", "great", "wonderful"],
            "helpful": ["helpful", "helped", "support"],
            "quick": ["quick", "fast", "speedy", "efficient"],
            "slow": ["slow", "delayed", "late", "waiting"],
            "professional": ["professional", "expert"],
            "poor": ["poor", "bad", "terrible", "worst"],
        }
        
        for key, words in keyword_map.items():
            if any(w in feedback_lower for w in words):
                keywords.append(key)
        
        survey = SatisfactionSurvey(
            id=str(uuid.uuid4()),
            case_id=case_id,
            user_id=user_id,
            rating=rating,
            would_recommend=would_recommend,
            feedback=feedback,
            keywords=keywords,
            submitted_at=datetime.now(),
        )
        
        self.surveys[survey.id] = survey
        return survey
    
    def calculate_nps(self) -> Dict:
        """Calculate Net Promoter Score"""
        if not self.surveys:
            return {"nps": 0, "promoters": 0, "passives": 0, "detractors": 0, "total": 0}
        
        promoters = sum(1 for s in self.surveys.values() if s.would_recommend and s.rating >= 4)
        detractors = sum(1 for s in self.surveys.values() if s.rating <= 2)
        total = len(self.surveys)
        passives = total - promoters - detractors
        
        nps = ((promoters - detractors) / total) * 100 if total > 0 else 0
        
        return {
            "nps": round(nps, 1),
            "promoters": promoters,
            "passives": passives,
            "detractors": detractors,
            "total": total,
            "promoter_pct": round(promoters / total * 100, 1) if total else 0,
            "detractor_pct": round(detractors / total * 100, 1) if total else 0,
        }
    
    def get_keyword_analysis(self) -> Dict:
        """Analyze feedback keywords"""
        all_keywords = []
        for survey in self.surveys.values():
            all_keywords.extend(survey.keywords)
        
        keyword_counts = Counter(all_keywords)
        
        positive = sum(keyword_counts.get(k, 0) for k in ["excellent", "helpful", "quick", "professional"])
        negative = sum(keyword_counts.get(k, 0) for k in ["slow", "poor"])
        
        return {
            "keyword_frequency": dict(keyword_counts.most_common(10)),
            "positive_sentiment": positive,
            "negative_sentiment": negative,
            "sentiment_ratio": round(positive / negative, 2) if negative > 0 else float('inf'),
        }
    
    def get_rating_distribution(self) -> Dict:
        """Get rating distribution"""
        ratings = [s.rating for s in self.surveys.values()]
        distribution = Counter(ratings)
        
        total = len(ratings)
        avg = sum(ratings) / total if total else 0
        
        return {
            "distribution": {str(i): distribution.get(i, 0) for i in range(1, 6)},
            "total_responses": total,
            "average_rating": round(avg, 2),
        }


# Singleton
_analytics_service: Optional[AnalyticsService] = None

def get_analytics_service() -> AnalyticsService:
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
