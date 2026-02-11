"""
DOER Platform - Documents Router

Handles file uploads, downloads, and document management for cases.

PRODUCTION UPGRADES:
- Add virus scanning before accepting uploads (ClamAV)
- Implement background OCR processing with Tesseract
- Add document classification via AI
- Generate presigned URLs for direct S3 downloads
- Add document versioning
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.database import get_db
from app.models import Document, Case, User, DocumentType, UserRole
from app.schemas import DocumentResponse, DocumentListResponse, MessageResponse
from app.services.auth import get_current_user
from app.services.storage import get_storage_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    case_id: int = Form(...),
    document_type: DocumentType = Form(default=DocumentType.OTHER),
    description: Optional[str] = Form(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document to a case.
    
    Supported file types: PDF, JPG, JPEG, PNG, DOC, DOCX
    Maximum file size: 50MB
    
    The document is stored locally and metadata is saved to the database.
    
    PRODUCTION:
    - Store in S3 with server-side encryption
    - Trigger background OCR processing
    - Run virus scan before accepting
    - Generate AI summary
    """
    # Verify case exists and user has access
    result = await db.execute(
        select(Case)
        .where(Case.id == case_id)
        .where(Case.is_deleted == False)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Check access permissions
    if current_user.role == UserRole.CLIENT and case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this case"
        )
    
    # Save file using storage service
    storage = get_storage_service()
    stored_filename, file_path, file_size = await storage.save_file(
        file, case_id, current_user.id
    )
    
    # Create document record
    document = Document(
        filename=stored_filename,
        original_filename=file.filename or "uploaded_file",
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        document_type=document_type,
        description=description,
        case_id=case_id,
        uploaded_by=current_user.id,
        is_processed=False,
        created_at=datetime.utcnow()
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # PRODUCTION: Trigger background processing
    # await process_document.delay(document.id)  # Celery task
    
    return document


@router.get("/{document_id}", response_class=StreamingResponse)
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download a document by its ID.
    
    Returns the file as a streaming response.
    
    PRODUCTION:
    - Return presigned S3 URL instead of streaming through API
    - Log download for audit trail
    - Check document-level permissions
    """
    # Fetch document with case info
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Verify access to the associated case
    result = await db.execute(
        select(Case)
        .where(Case.id == document.case_id)
        .where(Case.is_deleted == False)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated case not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.CLIENT and case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this document"
        )
    
    # Get file from storage
    storage = get_storage_service()
    file_content = await storage.get_file(document.file_path)
    
    # PRODUCTION: Log download
    # await log_document_access(document.id, current_user.id, "download")
    
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=document.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{document.original_filename}"',
            "Content-Length": str(len(file_content))
        }
    )


@router.get("/{document_id}/metadata", response_model=DocumentResponse)
async def get_document_metadata(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get document metadata without downloading the file.
    """
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Verify access
    result = await db.execute(
        select(Case)
        .where(Case.id == document.case_id)
        .where(Case.is_deleted == False)
    )
    case = result.scalar_one_or_none()
    
    if current_user.role == UserRole.CLIENT and case and case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this document"
        )
    
    return document


@router.get("/case/{case_id}", response_model=DocumentListResponse)
async def list_case_documents(
    case_id: int,
    document_type: Optional[DocumentType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all documents for a specific case.
    
    Optionally filter by document type.
    """
    # Verify case access
    result = await db.execute(
        select(Case)
        .where(Case.id == case_id)
        .where(Case.is_deleted == False)
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    if current_user.role == UserRole.CLIENT and case.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this case"
        )
    
    # Build query
    query = select(Document).where(Document.case_id == case_id)
    
    if document_type:
        query = query.where(Document.document_type == document_type)
    
    query = query.order_by(Document.created_at.desc())
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=len(documents)
    )


@router.delete("/{document_id}", response_model=MessageResponse)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document.
    
    Only the document uploader or admin can delete documents.
    The actual file is also removed from storage.
    
    PRODUCTION:
    - Soft delete to maintain audit trail
    - S3 versioning allows recovery if needed
    """
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.CLIENT and document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete documents you uploaded"
        )
    
    # Delete file from storage
    storage = get_storage_service()
    await storage.delete_file(document.file_path)
    
    # Delete database record
    await db.delete(document)
    await db.commit()
    
    return MessageResponse(
        message="Document deleted successfully",
        success=True
    )
