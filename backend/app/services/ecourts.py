"""
e-Courts Integration Service - Mock Version
Interface for court case filing status
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import uuid
import random
import asyncio
import logging

logger = logging.getLogger("E_COURTS")


class CaseType(str, Enum):
    CIVIL = "civil"
    REVENUE = "revenue"
    LAND_DISPUTE = "land_dispute"
    PROPERTY = "property"
    MUTATION = "mutation"


class CaseStatus(str, Enum):
    FILED = "filed"
    PENDING = "pending"
    LISTED = "listed"
    HEARING = "hearing"
    RESERVED = "reserved"
    DISPOSED = "disposed"
    DISMISSED = "dismissed"


@dataclass
class CourtCase:
    cnr_number: str  # Case Number Record
    case_type: CaseType
    filing_date: datetime
    petitioner: str
    respondent: str
    court: str
    judge: str
    status: CaseStatus
    next_hearing: Optional[datetime]
    orders: List[Dict]
    
    def to_dict(self):
        return {
            "cnr_number": self.cnr_number,
            "case_type": self.case_type.value,
            "filing_date": self.filing_date.isoformat(),
            "petitioner": self.petitioner,
            "respondent": self.respondent,
            "court": self.court,
            "judge": self.judge,
            "status": self.status.value,
            "next_hearing": self.next_hearing.isoformat() if self.next_hearing else None,
            "orders": self.orders,
        }


class ECourtsService:
    """
    Mock e-Courts Integration
    Interface structure ready for actual integration
    """
    
    def __init__(self):
        self.cases: Dict[str, CourtCase] = {}
        self._seed_mock_cases()
    
    def _seed_mock_cases(self):
        """Create mock court cases"""
        mock_cases = [
            ("MHPU01-000123-2026", CaseType.LAND_DISPUTE, "Ramesh Patil", "State of Maharashtra", "Pune District Court", "Hon. Justice A.K. Sharma"),
            ("MHPU01-000456-2026", CaseType.PROPERTY, "Sunita Patil", "Anil Jadhav", "Pune District Court", "Hon. Justice M.L. Kulkarni"),
            ("UPVR01-000789-2025", CaseType.REVENUE, "Krishna Rao", "Revenue Dept.", "Varanasi Court", "Hon. Justice R. Singh"),
            ("KABG01-001234-2026", CaseType.MUTATION, "Venkat Reddy", "Talathi Office", "Bangalore Rural Court", "Hon. Justice P. Rao"),
            ("TNCH01-005678-2025", CaseType.CIVIL, "Murugan K", "Chennai Corporation", "Chennai City Court", "Hon. Justice S. Kumar"),
        ]
        
        for i, (cnr, ctype, pet, resp, court, judge) in enumerate(mock_cases):
            days_ago = random.randint(30, 365)
            next_hearing = datetime.now() + timedelta(days=random.randint(7, 60))
            
            self.cases[cnr] = CourtCase(
                cnr_number=cnr,
                case_type=ctype,
                filing_date=datetime.now() - timedelta(days=days_ago),
                petitioner=pet,
                respondent=resp,
                court=court,
                judge=judge,
                status=random.choice(list(CaseStatus)),
                next_hearing=next_hearing if random.random() > 0.3 else None,
                orders=[
                    {"date": (datetime.now() - timedelta(days=days_ago-10)).isoformat(),
                     "order": "Case admitted for hearing"},
                    {"date": (datetime.now() - timedelta(days=days_ago-30)).isoformat(),
                     "order": "Notice issued to respondent"},
                ]
            )
    
    async def get_case_status(self, cnr_number: str) -> Optional[Dict]:
        """Get case status by CNR number"""
        await asyncio.sleep(random.uniform(0.3, 0.8))  # Simulate API latency
        
        case = self.cases.get(cnr_number.upper())
        if case:
            return case.to_dict()
        return None
    
    async def file_case(
        self,
        case_type: CaseType,
        petitioner: str,
        respondent: str,
        court: str,
        description: str,
        documents: List[str],
    ) -> Dict:
        """File a new court case (mock)"""
        await asyncio.sleep(random.uniform(0.5, 1.0))
        
        # Generate CNR number
        state_code = "MH" if "Maharashtra" in court else "UP"
        district_code = "PU" if "Pune" in court else "VR"
        cnr = f"{state_code}{district_code}01-{random.randint(100000, 999999)}-{datetime.now().year}"
        
        new_case = CourtCase(
            cnr_number=cnr,
            case_type=case_type,
            filing_date=datetime.now(),
            petitioner=petitioner,
            respondent=respondent,
            court=court,
            judge="To be assigned",
            status=CaseStatus.FILED,
            next_hearing=datetime.now() + timedelta(days=random.randint(14, 30)),
            orders=[{"date": datetime.now().isoformat(), "order": "Case filed successfully"}],
        )
        
        self.cases[cnr] = new_case
        
        return {
            "success": True,
            "cnr_number": cnr,
            "filing_date": new_case.filing_date.isoformat(),
            "status": "Filed successfully",
            "next_steps": "Await court notice for first hearing date",
        }
    
    async def search_cases(
        self,
        petitioner: str = None,
        respondent: str = None,
        case_type: CaseType = None,
        status: CaseStatus = None,
    ) -> List[Dict]:
        """Search cases by criteria"""
        await asyncio.sleep(0.3)
        
        results = []
        for case in self.cases.values():
            if petitioner and petitioner.lower() not in case.petitioner.lower():
                continue
            if respondent and respondent.lower() not in case.respondent.lower():
                continue
            if case_type and case.case_type != case_type:
                continue
            if status and case.status != status:
                continue
            results.append(case.to_dict())
        
        return results


# Singleton
_ecourts_service: Optional[ECourtsService] = None

def get_ecourts_service() -> ECourtsService:
    global _ecourts_service
    if _ecourts_service is None:
        _ecourts_service = ECourtsService()
    return _ecourts_service
