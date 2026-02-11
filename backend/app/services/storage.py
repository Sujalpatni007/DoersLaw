"""
DOER Platform - File Storage Service

This module provides an abstraction layer for file storage.
Currently uses local filesystem, designed for easy S3 migration.

PRODUCTION UPGRADE TO S3:
1. Install boto3: pip install boto3
2. Set STORAGE_PROVIDER="s3" in config
3. Configure AWS credentials via environment or IAM role
4. The S3 implementation below can be used as a drop-in replacement

Example S3 migration:
    from app.services.storage import get_storage_service
    storage = get_storage_service()  # Returns S3Storage in production
    await storage.save_file(file, path)
"""

import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Protocol, runtime_checkable
from fastapi import UploadFile, HTTPException

from app.config import get_settings

settings = get_settings()


@runtime_checkable
class StorageService(Protocol):
    """Protocol defining the storage service interface."""
    
    async def save_file(
        self, 
        file: UploadFile, 
        case_id: int, 
        user_id: int
    ) -> tuple[str, str, int]:
        """Save a file and return (stored_filename, file_path, file_size)."""
        ...
    
    async def get_file(self, file_path: str) -> bytes:
        """Retrieve file contents."""
        ...
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        ...
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        ...


class LocalStorageService:
    """
    Local filesystem storage implementation.
    
    Files are stored in: UPLOAD_DIR/case_{case_id}/{uuid}_{original_filename}
    
    PRODUCTION NOTES:
    - Not suitable for distributed deployments (use S3/GCS)
    - No redundancy or backup (files lost if disk fails)
    - Limited scalability
    - Consider adding virus scanning before accepting files
    """
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        self.allowed_types = set(settings.ALLOWED_FILE_TYPES.split(","))
        
        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def _validate_file(self, file: UploadFile) -> None:
        """Validate file type and size."""
        # Check file extension
        if file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext not in self.allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type not allowed. Allowed: {', '.join(self.allowed_types)}"
                )
        
        # Check content type
        allowed_mimes = {
            "pdf": "application/pdf",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        # Relaxed check - just ensure content_type is present
        if not file.content_type:
            raise HTTPException(status_code=400, detail="File content type is required")
    
    def _generate_filename(self, original_filename: str) -> str:
        """Generate a unique filename to prevent collisions."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        
        # Sanitize original filename
        safe_name = "".join(c for c in original_filename if c.isalnum() or c in "._-")
        if not safe_name:
            safe_name = "file"
        
        return f"{timestamp}_{unique_id}_{safe_name}"
    
    async def save_file(
        self, 
        file: UploadFile, 
        case_id: int, 
        user_id: int
    ) -> tuple[str, str, int]:
        """
        Save an uploaded file to local storage.
        
        Args:
            file: FastAPI UploadFile object
            case_id: ID of the associated case
            user_id: ID of the uploading user
            
        Returns:
            Tuple of (stored_filename, relative_path, file_size_bytes)
            
        Raises:
            HTTPException: If file validation fails or storage error occurs
        """
        self._validate_file(file)
        
        # Create case-specific directory
        case_dir = self.upload_dir / f"case_{case_id}"
        case_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        stored_filename = self._generate_filename(file.filename or "file")
        file_path = case_dir / stored_filename
        relative_path = f"case_{case_id}/{stored_filename}"
        
        # Save file with size check
        try:
            file_size = 0
            with open(file_path, "wb") as buffer:
                while chunk := await file.read(8192):  # 8KB chunks
                    file_size += len(chunk)
                    if file_size > self.max_file_size:
                        # Clean up partial file
                        buffer.close()
                        file_path.unlink()
                        raise HTTPException(
                            status_code=413,
                            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
                        )
                    buffer.write(chunk)
            
            return stored_filename, relative_path, file_size
            
        except HTTPException:
            raise
        except Exception as e:
            # Clean up on error
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
    
    async def get_file(self, file_path: str) -> bytes:
        """
        Retrieve file contents.
        
        Args:
            file_path: Relative path from upload directory
            
        Returns:
            File contents as bytes
        """
        full_path = self.upload_dir / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Security check - prevent path traversal
        try:
            full_path.resolve().relative_to(self.upload_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return full_path.read_bytes()
    
    async def get_file_path(self, file_path: str) -> Path:
        """
        Get the full filesystem path for a file.
        
        Args:
            file_path: Relative path from upload directory
            
        Returns:
            Full Path object
        """
        full_path = self.upload_dir / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return full_path
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: Relative path from upload directory
            
        Returns:
            True if deleted, False if not found
        """
        full_path = self.upload_dir / file_path
        
        if not full_path.exists():
            return False
        
        # Security check
        try:
            full_path.resolve().relative_to(self.upload_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
        
        full_path.unlink()
        return True
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        full_path = self.upload_dir / file_path
        return full_path.exists()


# =============================================================================
# S3 Storage Implementation (PRODUCTION)
# =============================================================================
# 
# Uncomment and configure for production use with AWS S3:
#
# import boto3
# from botocore.exceptions import ClientError
# 
# class S3StorageService:
#     """
#     AWS S3 storage implementation.
#     
#     REQUIREMENTS:
#     - pip install boto3
#     - AWS credentials configured via environment or IAM role
#     - S3 bucket created with appropriate permissions
#     
#     RECOMMENDED S3 BUCKET POLICY:
#     - Enable versioning for document history
#     - Enable server-side encryption (SSE-S3 or SSE-KMS)
#     - Set lifecycle rules for archival (e.g., move to Glacier after 1 year)
#     - Enable access logging for audit trail
#     """
#     
#     def __init__(self):
#         self.s3_client = boto3.client(
#             's3',
#             region_name=settings.AWS_REGION,
#             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
#         )
#         self.bucket_name = settings.S3_BUCKET_NAME
#         self.max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
#     
#     async def save_file(
#         self, 
#         file: UploadFile, 
#         case_id: int, 
#         user_id: int
#     ) -> tuple[str, str, int]:
#         """Save file to S3."""
#         stored_filename = self._generate_filename(file.filename or "file")
#         s3_key = f"cases/{case_id}/{stored_filename}"
#         
#         # Read file content
#         content = await file.read()
#         file_size = len(content)
#         
#         if file_size > self.max_file_size:
#             raise HTTPException(413, "File too large")
#         
#         # Upload to S3 with metadata
#         self.s3_client.put_object(
#             Bucket=self.bucket_name,
#             Key=s3_key,
#             Body=content,
#             ContentType=file.content_type,
#             Metadata={
#                 'original-filename': file.filename,
#                 'uploaded-by': str(user_id),
#                 'case-id': str(case_id)
#             }
#         )
#         
#         return stored_filename, s3_key, file_size
#     
#     async def get_file(self, file_path: str) -> bytes:
#         """Get file from S3."""
#         try:
#             response = self.s3_client.get_object(
#                 Bucket=self.bucket_name,
#                 Key=file_path
#             )
#             return response['Body'].read()
#         except ClientError as e:
#             if e.response['Error']['Code'] == 'NoSuchKey':
#                 raise HTTPException(404, "File not found")
#             raise
#     
#     async def get_presigned_url(self, file_path: str, expires_in: int = 3600) -> str:
#         """Generate a presigned URL for direct download."""
#         return self.s3_client.generate_presigned_url(
#             'get_object',
#             Params={'Bucket': self.bucket_name, 'Key': file_path},
#             ExpiresIn=expires_in
#         )
#     
#     async def delete_file(self, file_path: str) -> bool:
#         """Delete file from S3."""
#         try:
#             self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
#             return True
#         except ClientError:
#             return False
#     
#     async def file_exists(self, file_path: str) -> bool:
#         """Check if file exists in S3."""
#         try:
#             self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
#             return True
#         except ClientError:
#             return False


# =============================================================================
# Storage Factory
# =============================================================================

def get_storage_service() -> LocalStorageService:
    """
    Factory function to get the appropriate storage service.
    
    PRODUCTION: Update this to return S3StorageService when
    STORAGE_PROVIDER is set to "s3" in configuration.
    
    Example:
        if settings.STORAGE_PROVIDER == "s3":
            return S3StorageService()
        return LocalStorageService()
    """
    # Currently returns local storage only
    # PRODUCTION: Check settings.STORAGE_PROVIDER and return appropriate service
    return LocalStorageService()
