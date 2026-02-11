"""
DOER Platform - Verification API Router

Endpoints for document upload, processing, and verification.

ENDPOINTS:
- POST /verification/upload-document - Upload and process document
- GET /verification/verify-documents/{case_id} - Verify case documents
- GET /verification/land-records/search - Search mock land records
- GET /verification/land-records/stats - Get database statistics

PRODUCTION UPGRADES:
- Add rate limiting per user
- Implement background processing with Celery
- Add webhook notifications for async processing
- Implement audit logging
"""

from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Depends, status
from pydantic import BaseModel, Field

from app.services.document_processor import get_document_processor, SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_MB
from app.services.ocr_engine import get_ocr_engine
from app.services.land_records import get_land_records_service
from app.services.verification import get_verification_service
from app.services.auth import get_current_user
from app.models import User


router = APIRouter(prefix="/verification", tags=["Document Verification"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class DocumentUploadResponse(BaseModel):
    """Response for document upload."""
    success: bool
    message: str
    file_info: Optional[dict] = None
    ocr_result: Optional[dict] = None


class VerificationReportResponse(BaseModel):
    """Response for case verification."""
    case_id: int
    generated_at: str
    total_documents: int
    all_verified: bool
    total_critical_issues: int
    total_warnings: int
    recommendation: str
    document_reports: List[dict]


class LandRecordSearchResponse(BaseModel):
    """Response for land record search."""
    query: dict
    results: List[dict]
    count: int


class LandRecordStatsResponse(BaseModel):
    """Response for land record statistics."""
    total_records: int
    states: List[str]
    district_count: int
    total_area_acres: float


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/upload-document", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Document file (PDF, JPG, PNG)"),
    case_id: int = Form(..., description="Case ID to associate document with"),
    process_ocr: bool = Form(True, description="Run OCR text extraction"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document for processing.
    
    Supports PDF, JPG, PNG files up to 10MB.
    Optionally runs OCR to extract text and structured data.
    """
    processor = get_document_processor()
    
    # Validate file type
    content_type = file.content_type or ""
    if content_type not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {content_type}. Supported: PDF, JPG, PNG"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Validate file size
    is_valid, error = processor.validate_file(content_type, file_size)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Save document
    file_info = await processor.save_document(
        content=content,
        case_id=case_id,
        content_type=content_type,
        original_filename=file.filename or "unknown"
    )
    
    # Run OCR if requested
    ocr_result = None
    if process_ocr:
        from pathlib import Path
        file_path = Path(file_info["file_path"])
        
        ocr_engine = get_ocr_engine()
        ocr_result = await ocr_engine.process_document(file_path)
    
    return DocumentUploadResponse(
        success=True,
        message="Document uploaded successfully",
        file_info=file_info,
        ocr_result=ocr_result
    )


@router.get("/verify-documents/{case_id}", response_model=VerificationReportResponse)
async def verify_case_documents(
    case_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Verify all documents for a case against land records.
    
    Runs OCR on unprocessed documents and cross-references with
    the mock Bhulekh API. Returns a comprehensive verification report.
    """
    processor = get_document_processor()
    ocr_engine = get_ocr_engine()
    verification_service = get_verification_service()
    
    # Get case documents
    documents = processor.list_case_documents(case_id)
    
    if not documents:
        return VerificationReportResponse(
            case_id=case_id,
            generated_at="",
            total_documents=0,
            all_verified=False,
            total_critical_issues=0,
            total_warnings=0,
            recommendation="No documents found for this case. Please upload land documents first.",
            document_reports=[]
        )
    
    # Process each document
    document_extractions = []
    
    from pathlib import Path
    for idx, doc in enumerate(documents):
        file_path = Path(doc["file_path"])
        
        # Run OCR
        ocr_result = await ocr_engine.process_document(file_path)
        
        if ocr_result.get("success"):
            document_extractions.append({
                "document_id": idx + 1,
                "filename": doc["filename"],
                "extracted_data": ocr_result.get("extracted_data", {})
            })
    
    # Generate verification report
    report = verification_service.generate_case_verification_report(
        case_id=case_id,
        document_extractions=document_extractions
    )
    
    return VerificationReportResponse(**report)


@router.get("/land-records/search", response_model=LandRecordSearchResponse)
async def search_land_records(
    survey_number: Optional[str] = Query(None, description="Survey number to search"),
    khasra_number: Optional[str] = Query(None, description="Khasra number to search"),
    owner_name: Optional[str] = Query(None, description="Owner name to search"),
    village: Optional[str] = Query(None, description="Village name"),
    district: Optional[str] = Query(None, description="District name"),
    state: Optional[str] = Query(None, description="State name")
):
    """
    Search the mock Bhulekh land records database.
    
    This is a simulated API that returns sample land records.
    Useful for testing and demonstration purposes.
    """
    land_records = get_land_records_service()
    
    results = []
    query = {}
    
    # Build query info
    if survey_number:
        query["survey_number"] = survey_number
        result = land_records.search_by_survey_number(survey_number)
        if result:
            results.append(result)
    
    if khasra_number:
        query["khasra_number"] = khasra_number
        result = land_records.search_by_khasra(khasra_number)
        if result and result not in results:
            results.append(result)
    
    if owner_name:
        query["owner_name"] = owner_name
        owner_results = land_records.search_by_owner(owner_name)
        for r in owner_results:
            if r not in results:
                results.append(r)
    
    if village or district or state:
        query.update({
            k: v for k, v in {
                "village": village,
                "district": district,
                "state": state
            }.items() if v
        })
        location_results = land_records.search_by_location(
            village=village,
            district=district,
            state=state
        )
        for r in location_results:
            if r not in results:
                results.append(r)
    
    # If no query params, return all records
    if not query:
        results = land_records.list_all_records()
    
    return LandRecordSearchResponse(
        query=query,
        results=results,
        count=len(results)
    )


@router.get("/land-records/stats", response_model=LandRecordStatsResponse)
async def get_land_record_statistics():
    """
    Get statistics about the mock land records database.
    """
    land_records = get_land_records_service()
    stats = land_records.get_statistics()
    
    return LandRecordStatsResponse(**stats)


@router.get("/land-records/{record_id}")
async def get_land_record(record_id: str):
    """
    Get a specific land record by survey number.
    """
    land_records = get_land_records_service()
    
    result = land_records.search_by_survey_number(record_id)
    if not result:
        result = land_records.search_by_khasra(record_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Land record not found: {record_id}"
        )
    
    return result


@router.post("/demo/populate-records")
async def populate_demo_records():
    """
    Populate demo mode with sample land records.
    
    This endpoint ensures sample data is available for testing.
    """
    land_records = get_land_records_service()
    
    # Re-initialize to ensure data is saved
    land_records._initialize_records()
    
    return {
        "message": "Demo records populated successfully",
        "stats": land_records.get_statistics()
    }
