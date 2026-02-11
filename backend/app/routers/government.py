"""
Government Integration Router
API endpoints for Bhulekh, e-Courts, Digidhan, and PDF generation
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.services.bhulekh import get_bhulekh_service, VerificationStatus
from app.services.ecourts import get_ecourts_service, CaseType, CaseStatus
from app.services.digidhan import get_digidhan_service, PaymentType, PaymentMethod
from app.services.pdf_generator import get_pdf_generator

router = APIRouter(prefix="/gov", tags=["Government Integration"])


# =============================================================================
# Request Models
# =============================================================================

class LandVerificationRequest(BaseModel):
    state: str
    district: str
    tehsil: str
    village: str
    khasra: str
    claimed_owner: Optional[str] = None
    claimed_area: Optional[float] = None


class CaseFilingRequest(BaseModel):
    case_type: str  # civil, revenue, land_dispute, property, mutation
    petitioner: str
    respondent: str
    court: str
    description: str
    documents: List[str] = []


class PaymentRequest(BaseModel):
    user_id: int
    payment_type: str  # court_fee, stamp_duty, etc.
    amount: float
    method: str  # upi, netbanking, debit_card, credit_card
    case_id: Optional[str] = None


class FeeCalculationRequest(BaseModel):
    payment_type: str
    dispute_value: float = 0


# =============================================================================
# Bhulekh Endpoints
# =============================================================================

@router.post("/verify-land-record")
async def verify_land_record(request: LandVerificationRequest, developer_mode: bool = False):
    """
    Verify land record against Bhulekh database
    
    - **state**: State name (e.g., Maharashtra, Uttar Pradesh)
    - **district**: District name
    - **tehsil**: Tehsil/Taluka name
    - **village**: Village name
    - **khasra**: Khasra/Survey number
    - **claimed_owner**: (Optional) Owner name to verify
    - **claimed_area**: (Optional) Area in acres to verify
    - **developer_mode**: Show raw API response for debugging
    """
    service = get_bhulekh_service()
    service.set_developer_mode(developer_mode)
    
    result = await service.verify_land_record(
        state=request.state,
        district=request.district,
        tehsil=request.tehsil,
        village=request.village,
        khasra=request.khasra,
        claimed_owner=request.claimed_owner,
        claimed_area=request.claimed_area,
    )
    
    response = {
        "verification_id": result.verification_id,
        "status": result.status.value,
        "confidence": result.confidence,
        "discrepancies": result.discrepancies,
        "timestamp": result.timestamp.isoformat(),
    }
    
    if result.record:
        response["record"] = result.record.to_dict()
    
    if developer_mode and result.raw_response:
        response["_debug"] = result.raw_response
    
    return response


@router.get("/land-records/search")
async def search_land_records(
    state: str = None,
    district: str = None,
    owner: str = None,
    limit: int = Query(default=10, le=50),
):
    """Search land records by criteria"""
    service = get_bhulekh_service()
    records = service.search_records(
        state=state,
        district=district,
        owner=owner,
        limit=limit,
    )
    
    return {
        "count": len(records),
        "records": [r.to_dict() for r in records],
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """Get LRU cache statistics"""
    service = get_bhulekh_service()
    return service.get_cache_stats()


@router.post("/cache/clear")
async def clear_cache():
    """Clear LRU cache"""
    service = get_bhulekh_service()
    service.clear_cache()
    return {"status": "Cache cleared"}


# =============================================================================
# e-Courts Endpoints
# =============================================================================

@router.get("/ecourts/case/{cnr_number}")
async def get_case_status(cnr_number: str):
    """Get case status by CNR number"""
    service = get_ecourts_service()
    case = await service.get_case_status(cnr_number)
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return case


@router.post("/ecourts/file")
async def file_court_case(request: CaseFilingRequest):
    """File a new court case (mock)"""
    service = get_ecourts_service()
    
    # Map string to enum
    case_type_map = {
        "civil": CaseType.CIVIL,
        "revenue": CaseType.REVENUE,
        "land_dispute": CaseType.LAND_DISPUTE,
        "property": CaseType.PROPERTY,
        "mutation": CaseType.MUTATION,
    }
    case_type = case_type_map.get(request.case_type.lower())
    if not case_type:
        raise HTTPException(status_code=400, detail="Invalid case type")
    
    result = await service.file_case(
        case_type=case_type,
        petitioner=request.petitioner,
        respondent=request.respondent,
        court=request.court,
        description=request.description,
        documents=request.documents,
    )
    
    return result


@router.get("/ecourts/search")
async def search_cases(
    petitioner: str = None,
    respondent: str = None,
    case_type: str = None,
    status: str = None,
):
    """Search court cases"""
    service = get_ecourts_service()
    
    ct = None
    if case_type:
        ct = CaseType(case_type)
    
    st = None
    if status:
        st = CaseStatus(status)
    
    results = await service.search_cases(
        petitioner=petitioner,
        respondent=respondent,
        case_type=ct,
        status=st,
    )
    
    return {"count": len(results), "cases": results}


# =============================================================================
# Payment Endpoints
# =============================================================================

@router.post("/payment/calculate-fee")
async def calculate_fee(request: FeeCalculationRequest):
    """Calculate fees for a payment type"""
    service = get_digidhan_service()
    
    pt_map = {
        "court_fee": PaymentType.COURT_FEE,
        "stamp_duty": PaymentType.STAMP_DUTY,
        "registration_fee": PaymentType.REGISTRATION_FEE,
        "lawyer_fee": PaymentType.LAWYER_FEE,
        "service_fee": PaymentType.SERVICE_FEE,
    }
    
    payment_type = pt_map.get(request.payment_type.lower())
    if not payment_type:
        raise HTTPException(status_code=400, detail="Invalid payment type")
    
    return service.calculate_fee(
        payment_type=payment_type,
        dispute_value=request.dispute_value,
    )


@router.post("/payment/initiate")
async def initiate_payment(request: PaymentRequest):
    """Initiate a payment"""
    service = get_digidhan_service()
    
    pt_map = {
        "court_fee": PaymentType.COURT_FEE,
        "stamp_duty": PaymentType.STAMP_DUTY,
        "registration_fee": PaymentType.REGISTRATION_FEE,
        "lawyer_fee": PaymentType.LAWYER_FEE,
        "service_fee": PaymentType.SERVICE_FEE,
    }
    
    pm_map = {
        "upi": PaymentMethod.UPI,
        "netbanking": PaymentMethod.NETBANKING,
        "debit_card": PaymentMethod.DEBIT_CARD,
        "credit_card": PaymentMethod.CREDIT_CARD,
        "wallet": PaymentMethod.WALLET,
    }
    
    payment_type = pt_map.get(request.payment_type.lower())
    payment_method = pm_map.get(request.method.lower())
    
    if not payment_type or not payment_method:
        raise HTTPException(status_code=400, detail="Invalid payment type or method")
    
    payment = await service.initiate_payment(
        user_id=request.user_id,
        payment_type=payment_type,
        amount=request.amount,
        method=payment_method,
        case_id=request.case_id,
    )
    
    return payment.to_dict()


@router.post("/payment/process/{payment_id}")
async def process_payment(payment_id: str):
    """Process a payment (mock payment gateway)"""
    service = get_digidhan_service()
    return await service.process_payment(payment_id)


@router.get("/payment/{payment_id}")
async def get_payment_status(payment_id: str):
    """Get payment status"""
    service = get_digidhan_service()
    payment = await service.get_payment_status(payment_id)
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return payment


@router.get("/payment/user/{user_id}")
async def get_user_payments(user_id: int):
    """Get all payments for a user"""
    service = get_digidhan_service()
    return {"payments": service.get_user_payments(user_id)}


# =============================================================================
# Certificate Endpoints
# =============================================================================

@router.post("/certificate/verification")
async def generate_verification_certificate(
    verification_id: str,
    user_name: str,
    case_id: str = None,
):
    """Generate land record verification certificate PDF"""
    bhulekh = get_bhulekh_service()
    pdf_gen = get_pdf_generator()
    
    # For demo, use a mock record
    mock_record = {
        "state": "Maharashtra",
        "district": "Pune",
        "tehsil": "Haveli",
        "village": "Lohegaon",
        "khasra": "123/1",
        "owner": "Ramesh Patil",
        "area_acres": 2.5,
        "cultivation": "Agricultural",
        "encumbrances": "None",
    }
    
    filepath = pdf_gen.generate_verification_certificate(
        verification_id=verification_id,
        land_record=mock_record,
        verification_status="verified",
        confidence=0.95,
        discrepancies=[],
        user_name=user_name,
        case_id=case_id,
    )
    
    return {
        "certificate_id": verification_id,
        "filepath": filepath,
        "download_url": f"/api/v1/gov/download/{verification_id}",
    }


@router.get("/download/{certificate_id}")
async def download_certificate(certificate_id: str):
    """Download generated certificate"""
    import os
    
    # Check for verification cert
    filepath = f"/tmp/doer_certificates/verification_{certificate_id}.pdf"
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=f"verification_{certificate_id}.pdf")
    
    # Check for receipt
    filepath = f"/tmp/doer_certificates/receipt_{certificate_id}.pdf"
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=f"receipt_{certificate_id}.pdf")
    
    raise HTTPException(status_code=404, detail="Certificate not found")


# =============================================================================
# Developer Mode Toggle
# =============================================================================

@router.post("/developer-mode/{enabled}")
async def set_developer_mode(enabled: bool):
    """Toggle developer mode for raw API responses"""
    bhulekh = get_bhulekh_service()
    bhulekh.set_developer_mode(enabled)
    
    return {
        "developer_mode": enabled,
        "message": f"Developer mode {'enabled' if enabled else 'disabled'}",
    }
