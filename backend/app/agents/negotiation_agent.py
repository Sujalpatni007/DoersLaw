"""
DOER Platform - Negotiation Bot Agent

Rule-based settlement proposal generator.

FEATURES:
- Decision tree for settlement options
- Multiple proposal types (split, buyout, mediation)
- Land value estimation (mock data)
- Party claim analysis

PRODUCTION UPGRADES:
- ML-based fair value estimation
- Historical settlement analysis
- Multi-round negotiation support
- Party preference learning
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class SettlementType(str, Enum):
    """Types of settlement proposals."""
    EQUAL_SPLIT = "equal_split"
    WEIGHTED_SPLIT = "weighted_split"
    BUYOUT = "buyout"
    MEDIATION = "mediation"
    PARTITION = "partition"
    COMPENSATION = "compensation"


class ProposalStatus(str, Enum):
    """Proposal status values."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTER_PROPOSED = "counter_proposed"


@dataclass
class Claim:
    """Represents a party's claim."""
    party_name: str
    claimed_percentage: float  # 0-100
    claimed_area: Optional[float] = None  # in acres
    supporting_documents: int = 0
    years_of_possession: int = 0
    legal_basis: Optional[str] = None


@dataclass
class SettlementProposal:
    """A settlement proposal."""
    proposal_id: str
    case_id: int
    settlement_type: SettlementType
    title: str
    description: str
    terms: Dict[str, Any]
    status: ProposalStatus = ProposalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    confidence_score: float = 0.0
    rationale: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "case_id": self.case_id,
            "settlement_type": self.settlement_type.value,
            "title": self.title,
            "description": self.description,
            "terms": self.terms,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "confidence_score": self.confidence_score,
            "rationale": self.rationale
        }


# Mock land values by location (₹ per acre in lakhs)
MOCK_LAND_VALUES: Dict[str, float] = {
    "mumbai": 500.0,
    "pune": 80.0,
    "bangalore": 150.0,
    "delhi": 300.0,
    "lucknow": 40.0,
    "varanasi": 30.0,
    "nagpur": 25.0,
    "mysore": 45.0,
    "rural_default": 10.0,
    "urban_default": 50.0
}


class NegotiationAgent:
    """
    Rule-based negotiation bot for settlement proposals.
    
    Generates 2-3 settlement options based on:
    - Party claims
    - Land value
    - Dispute type
    - Supporting evidence
    """
    
    def __init__(self):
        """Initialize the negotiation agent."""
        self.proposals: Dict[str, SettlementProposal] = {}
        self.proposal_counter = 0
    
    def _generate_proposal_id(self, case_id: int) -> str:
        """Generate unique proposal ID."""
        self.proposal_counter += 1
        return f"PROP-{case_id}-{self.proposal_counter:03d}"
    
    def estimate_land_value(
        self,
        area_acres: float,
        location: str,
        land_type: str = "agricultural"
    ) -> Dict[str, Any]:
        """
        Estimate land value based on location and type.
        
        Args:
            area_acres: Land area in acres
            location: Location name
            land_type: Type of land
            
        Returns:
            Valuation details
        """
        # Get base rate
        location_key = location.lower()
        base_rate = MOCK_LAND_VALUES.get(
            location_key, 
            MOCK_LAND_VALUES.get(
                f"{land_type}_default",
                MOCK_LAND_VALUES["rural_default"]
            )
        )
        
        # Adjust for land type
        type_multipliers = {
            "agricultural": 1.0,
            "residential": 2.5,
            "commercial": 4.0,
            "industrial": 3.0
        }
        multiplier = type_multipliers.get(land_type, 1.0)
        
        # Calculate value
        rate_per_acre = base_rate * multiplier
        total_value = area_acres * rate_per_acre
        
        return {
            "area_acres": area_acres,
            "location": location,
            "land_type": land_type,
            "rate_per_acre_lakhs": rate_per_acre,
            "total_value_lakhs": total_value,
            "total_value_crores": total_value / 100,
            "estimation_basis": "market_average",
            "disclaimer": "This is an estimated value for negotiation purposes only"
        }
    
    def analyze_claims(
        self,
        party_1: Claim,
        party_2: Claim
    ) -> Dict[str, Any]:
        """
        Analyze competing claims to determine fair allocation.
        
        Returns:
            Analysis with recommended splits
        """
        # Score based on evidence
        def score_claim(claim: Claim) -> float:
            score = 0.0
            
            # Years of possession (max 30 points)
            score += min(claim.years_of_possession * 2, 30)
            
            # Supporting documents (max 30 points)
            score += min(claim.supporting_documents * 5, 30)
            
            # Claimed percentage as baseline (max 40 points)
            score += claim.claimed_percentage * 0.4
            
            return score
        
        score_1 = score_claim(party_1)
        score_2 = score_claim(party_2)
        total_score = score_1 + score_2
        
        if total_score == 0:
            ratio_1, ratio_2 = 50, 50
        else:
            ratio_1 = round((score_1 / total_score) * 100)
            ratio_2 = 100 - ratio_1
        
        return {
            "party_1": {
                "name": party_1.party_name,
                "score": score_1,
                "recommended_share": ratio_1
            },
            "party_2": {
                "name": party_2.party_name,
                "score": score_2,
                "recommended_share": ratio_2
            },
            "analysis_factors": [
                "years_of_possession",
                "supporting_documents",
                "claimed_percentage"
            ]
        }
    
    def generate_proposals(
        self,
        case_id: int,
        dispute_type: str,
        party_1: Claim,
        party_2: Claim,
        land_value: Dict[str, Any]
    ) -> List[SettlementProposal]:
        """
        Generate 2-3 settlement proposals.
        
        Args:
            case_id: Case ID
            dispute_type: Type of dispute
            party_1: First party's claim
            party_2: Second party's claim
            land_value: Land valuation data
            
        Returns:
            List of settlement proposals
        """
        proposals = []
        analysis = self.analyze_claims(party_1, party_2)
        total_value = land_value.get("total_value_lakhs", 100)
        area = land_value.get("area_acres", 1)
        
        share_1 = analysis["party_1"]["recommended_share"]
        share_2 = analysis["party_2"]["recommended_share"]
        
        # Proposal 1: Weighted Split based on claim analysis
        if dispute_type in ["ownership_dispute", "inheritance_dispute"]:
            prop_1 = SettlementProposal(
                proposal_id=self._generate_proposal_id(case_id),
                case_id=case_id,
                settlement_type=SettlementType.WEIGHTED_SPLIT,
                title=f"Weighted Split ({share_1}-{share_2})",
                description=f"Divide the property based on evidence-weighted claims: {party_1.party_name} gets {share_1}%, {party_2.party_name} gets {share_2}%",
                terms={
                    "party_1_share": share_1,
                    "party_2_share": share_2,
                    "party_1_area": round(area * share_1 / 100, 2),
                    "party_2_area": round(area * share_2 / 100, 2),
                    "party_1_value": round(total_value * share_1 / 100, 2),
                    "party_2_value": round(total_value * share_2 / 100, 2)
                },
                confidence_score=0.75,
                rationale=f"Based on {party_1.years_of_possession + party_2.years_of_possession} combined years of possession and {party_1.supporting_documents + party_2.supporting_documents} supporting documents"
            )
            proposals.append(prop_1)
        
        # Proposal 2: Buyout option
        buyout_amount = round(total_value * share_2 / 100, 2)
        prop_2 = SettlementProposal(
            proposal_id=self._generate_proposal_id(case_id),
            case_id=case_id,
            settlement_type=SettlementType.BUYOUT,
            title=f"Buyout at ₹{buyout_amount} Lakhs",
            description=f"{party_1.party_name} buys out {party_2.party_name}'s share at market value",
            terms={
                "buyer": party_1.party_name,
                "seller": party_2.party_name,
                "buyout_amount_lakhs": buyout_amount,
                "payment_terms": "50% upfront, 50% within 6 months",
                "transfer_timeline": "Complete within 90 days of payment"
            },
            confidence_score=0.65,
            rationale="Buyout provides clean resolution with single ownership"
        )
        proposals.append(prop_2)
        
        # Proposal 3: Mediation/Compensation for boundary/encroachment
        if dispute_type in ["boundary_dispute", "encroachment"]:
            encroached_area = min(area * 0.1, 0.5)  # Assume 10% or 0.5 acres
            compensation = round(encroached_area * land_value.get("rate_per_acre_lakhs", 50), 2)
            
            prop_3 = SettlementProposal(
                proposal_id=self._generate_proposal_id(case_id),
                case_id=case_id,
                settlement_type=SettlementType.COMPENSATION,
                title=f"Compensation of ₹{compensation} Lakhs + Restoration",
                description=f"Encroaching party pays compensation and restores boundaries",
                terms={
                    "encroached_area": encroached_area,
                    "compensation_lakhs": compensation,
                    "restoration_timeline": "30 days",
                    "boundary_demarcation": "Joint survey within 15 days"
                },
                confidence_score=0.70,
                rationale="Appropriate for encroachment cases with clear boundaries"
            )
            proposals.append(prop_3)
        else:
            # Equal split as alternative
            prop_3 = SettlementProposal(
                proposal_id=self._generate_proposal_id(case_id),
                case_id=case_id,
                settlement_type=SettlementType.EQUAL_SPLIT,
                title="Equal 50-50 Split",
                description=f"Equal division of property between both parties",
                terms={
                    "party_1_share": 50,
                    "party_2_share": 50,
                    "party_1_area": round(area / 2, 2),
                    "party_2_area": round(area / 2, 2)
                },
                confidence_score=0.60,
                rationale="Simple equal division when claims are comparable"
            )
            proposals.append(prop_3)
        
        # Store proposals
        for prop in proposals:
            self.proposals[prop.proposal_id] = prop
        
        return proposals
    
    def update_proposal_status(
        self,
        proposal_id: str,
        new_status: ProposalStatus,
        counter_terms: Optional[Dict[str, Any]] = None
    ) -> Optional[SettlementProposal]:
        """Update proposal status."""
        if proposal_id not in self.proposals:
            return None
        
        proposal = self.proposals[proposal_id]
        proposal.status = new_status
        
        if counter_terms and new_status == ProposalStatus.COUNTER_PROPOSED:
            proposal.terms["counter_proposal"] = counter_terms
        
        return proposal
    
    def get_case_proposals(self, case_id: int) -> List[Dict[str, Any]]:
        """Get all proposals for a case."""
        return [p.to_dict() for p in self.proposals.values() if p.case_id == case_id]


# Singleton instance  
_agent: Optional[NegotiationAgent] = None


def get_negotiation_agent() -> NegotiationAgent:
    """Get or create the negotiation agent instance."""
    global _agent
    if _agent is None:
        _agent = NegotiationAgent()
    return _agent
