"""
Case Analysis Router
Handles case intake data and Gemini API analysis
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import google.generativeai as genai

router = APIRouter(prefix="/case", tags=["case"])

# Configure Gemini with provided API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyA1T-py700AN5QfWaF-2e-LAo8E53DB8SE")
genai.configure(api_key=GEMINI_API_KEY)


class CaseIntakeData(BaseModel):
    location: str
    property_type: str
    possession_status: str
    opponent_type: str
    core_issue: str
    ancestral_status: str
    revenue_records_name: str
    documents_held: List[str]
    police_court_status: str
    immediate_threat: str
    dispute_start_date: str
    desired_outcome: str


class CaseAnalysis(BaseModel):
    summary: str
    legal_category: str
    severity_tier: str
    limitation_status: str
    risk_warning: Optional[str] = None


class OfficialPortalLink(BaseModel):
    name: str
    url: str
    purpose: str


class PoliceAction(BaseModel):
    step: str
    legal_code: str


class ActionableResources(BaseModel):
    official_portal_links: List[OfficialPortalLink]
    police_action: Optional[PoliceAction] = None


class DocumentChecklistItem(BaseModel):
    document: str
    source: str
    urgency: str


class RecommendedService(BaseModel):
    product_name: str
    price_point: str
    cta_text: str


class CaseAnalysisResponse(BaseModel):
    case_analysis: CaseAnalysis
    actionable_resources: ActionableResources
    smart_document_checklist: List[DocumentChecklistItem]
    immediate_next_steps: List[str]
    recommended_service: RecommendedService


def build_analysis_prompt(data: CaseIntakeData) -> str:
    """Build the Gemini prompt for case analysis"""
    return f"""You are an expert Indian legal analyst specializing in land and property disputes. 
Analyze the following case intake data and provide a comprehensive legal analysis.

## User Case Data:
{{
  "location": "{data.location}",
  "property_type": "{data.property_type}",
  "possession_status": "{data.possession_status}",
  "opponent_type": "{data.opponent_type}",
  "core_issue": "{data.core_issue}",
  "ancestral_status": "{data.ancestral_status}",
  "revenue_records_name": "{data.revenue_records_name}",
  "documents_held": {json.dumps(data.documents_held)},
  "police_court_status": "{data.police_court_status}",
  "immediate_threat": "{data.immediate_threat}",
  "dispute_start_date": "{data.dispute_start_date}",
  "desired_outcome": "{data.desired_outcome}"
}}

## Instructions:
Based on Indian property and land laws, provide a detailed analysis in the following EXACT JSON format:

{{
  "case_analysis": {{
    "summary": "A 2-3 sentence summary of the case situation and key legal considerations",
    "legal_category": "The specific legal category (e.g., 'Suit for Recovery of Possession (Section 5, Specific Relief Act)')",
    "severity_tier": "Severity level (e.g., 'CRITICAL (Level 9/10)', 'HIGH (Level 7/10)', 'MODERATE (Level 5/10)')",
    "limitation_status": "Status under Limitation Act (e.g., 'Valid. (Within 12 years limit per Article 65).')",
    "risk_warning": "Any critical warning the user should know (or null if none)"
  }},
  "actionable_resources": {{
    "official_portal_links": [
      {{
        "name": "Name of the government portal",
        "url": "URL to the portal",
        "purpose": "What the user can do on this portal"
      }}
    ],
    "police_action": {{
      "step": "Recommended police action step",
      "legal_code": "Relevant IPC sections"
    }}
  }},
  "smart_document_checklist": [
    {{
      "document": "Document name",
      "source": "Where to get it",
      "urgency": "High/Medium/Low with explanation"
    }}
  ],
  "immediate_next_steps": [
    "Step 1 with specific actionable instruction",
    "Step 2 with specific actionable instruction",
    "Step 3 with specific actionable instruction"
  ],
  "recommended_service": {{
    "product_name": "Recommended legal service",
    "price_point": "Price tier or 'Custom Quote'",
    "cta_text": "Call to action button text"
  }}
}}

IMPORTANT: 
- Include state-specific government portal links based on the location provided
- Provide at least 3-4 documents in the checklist
- Provide at least 3 immediate next steps
- Make the advice specific to Indian law

Respond ONLY with the JSON object, no additional text or markdown code blocks."""


@router.post("/analyze", response_model=CaseAnalysisResponse)
async def analyze_case(data: CaseIntakeData):
    """
    Analyze case intake data using Gemini AI
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = build_analysis_prompt(data)
        
        response = model.generate_content(prompt)
        
        # Parse the JSON response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        analysis = json.loads(response_text.strip())
        
        return CaseAnalysisResponse(**analysis)
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Response text: {response_text}")
        return get_mock_analysis(data)
    except Exception as e:
        print(f"Gemini API error: {e}")
        return get_mock_analysis(data)


def get_mock_analysis(data: CaseIntakeData) -> CaseAnalysisResponse:
    """
    Generate a mock analysis when Gemini API fails
    """
    # Determine severity based on immediate threat
    severity = 5
    if "Construction" in data.immediate_threat:
        severity = 9
    elif "violence" in data.immediate_threat.lower():
        severity = 10
    elif "sell" in data.immediate_threat.lower():
        severity = 8
    
    # Determine limitation status
    is_time_barred = data.dispute_start_date == "More than 12 years ago" and \
                     data.possession_status == "The other party is in possession"
    
    limitation_status = "Valid. (Within 12 years limit per Article 65)." if not is_time_barred else \
                       "Warning: May be time-barred under Article 65 (12-year limitation)."
    
    # Determine legal category
    legal_category = "Civil Suit"
    if "Family" in data.opponent_type:
        legal_category = "Partition Suit (Civil Court)"
    elif "Tenant" in data.opponent_type:
        legal_category = "Eviction Suit (Rent Controller)"
    elif "occupied" in data.core_issue.lower():
        legal_category = "Suit for Recovery of Possession (Section 5, Specific Relief Act)"
    elif "fake documents" in data.core_issue.lower():
        legal_category = "Suit for Declaration + Cancellation of Documents"
    elif "blocking" in data.core_issue.lower():
        legal_category = "Easement Rights Suit"
    
    # Build state-specific portal links
    state = data.location.lower()
    portal_links = []
    
    if "maharashtra" in state:
        portal_links = [
            OfficialPortalLink(
                name="Mahabhulekh (Maharashtra Land Records)",
                url="https://bhulekh.mahabhumi.gov.in",
                purpose="Download digital 7/12 Extract and 8A entry."
            ),
            OfficialPortalLink(
                name="IGR Maharashtra",
                url="https://igrmaharashtra.gov.in",
                purpose="Search for registered Index-II documents."
            )
        ]
    elif "karnataka" in state:
        portal_links = [
            OfficialPortalLink(
                name="Bhoomi (Karnataka Land Records)",
                url="https://landrecords.karnataka.gov.in",
                purpose="Download RTC and Mutation details."
            ),
            OfficialPortalLink(
                name="Kaveri Online",
                url="https://kaverionline.karnataka.gov.in",
                purpose="Property registration and encumbrance certificate."
            )
        ]
    else:
        portal_links = [
            OfficialPortalLink(
                name="State Land Records Portal",
                url="https://dolr.gov.in",
                purpose="Access state land records through central portal."
            ),
            OfficialPortalLink(
                name="NLRMP Portal",
                url="https://nlrmp.nic.in",
                purpose="National Land Records Modernization Programme."
            )
        ]
    
    # Build risk warning
    risk_warning = None
    if severity >= 8:
        if "Construction" in data.immediate_threat:
            risk_warning = "Construction is active. If the structure is completed, courts may refuse demolition and only award compensation. You need an immediate 'Temporary Injunction' (Stay Order)."
        elif "sell" in data.immediate_threat.lower():
            risk_warning = "If the property is sold to a 'bonafide purchaser', recovery becomes extremely difficult. File for Lis Pendens immediately."
        elif "violence" in data.immediate_threat.lower():
            risk_warning = "Immediate police protection required. Consider filing for anticipatory bail if counter-allegations are expected."
    
    return CaseAnalysisResponse(
        case_analysis=CaseAnalysis(
            summary=f"You are facing {data.core_issue.lower()} on your {data.property_type.lower()} in {data.location}. Since the opponent is {data.opponent_type.lower()} and {data.possession_status.lower()}, this requires immediate legal attention.",
            legal_category=legal_category,
            severity_tier=f"{'CRITICAL' if severity >= 8 else 'HIGH' if severity >= 6 else 'MODERATE'} (Level {severity}/10)",
            limitation_status=limitation_status,
            risk_warning=risk_warning
        ),
        actionable_resources=ActionableResources(
            official_portal_links=portal_links,
            police_action=PoliceAction(
                step="Ensure your complaint is converted to an FIR if criminal trespass occurred.",
                legal_code="Section 441 (Criminal Trespass) & Section 447 IPC"
            ) if "Police" in data.police_court_status or severity >= 7 else None
        ),
        smart_document_checklist=[
            DocumentChecklistItem(
                document="7/12 Extract (Current)",
                source="State Land Records Portal or local Talathi/Patwari Office",
                urgency="High - proves your current legal ownership/possession."
            ),
            DocumentChecklistItem(
                document="Mutation Entry (Ferfar/Khata)",
                source="Revenue Department (Tehsil/Taluka Office)",
                urgency="High - traces history of title transfers."
            ),
            DocumentChecklistItem(
                document="Registered Sale Deed/Title Document",
                source="Sub-Registrar Office",
                urgency="High - primary proof of ownership."
            ),
            DocumentChecklistItem(
                document="Geo-Tagged Photographs",
                source="Self-Click (Use a timestamp camera app)",
                urgency="Immediate - proves current state and timeline."
            )
        ],
        immediate_next_steps=[
            "1. Take photos of the property/construction site with a daily newspaper in the frame (to prove date).",
            "2. Download the latest land record extract from the state portal to check for unauthorized changes.",
            "3. File a 'Written Complaint' to the local Police Station specifically mentioning the dispute and ask for an acknowledgement stamp.",
            "4. Consult a property lawyer within 48 hours to assess the need for an urgent court injunction."
        ],
        recommended_service=RecommendedService(
            product_name="Emergency Injunction Consultation" if severity >= 8 else "Legal Notice Drafting",
            price_point="Custom Quote (Urgent)" if severity >= 8 else "₹2,999",
            cta_text="Connect with Expert Lawyer" if severity >= 8 else "Get Legal Notice Drafted"
        )
    )
