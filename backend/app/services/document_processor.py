"""
DOER Platform - Document Processor Service

Handles document uploads, validation, and thumbnail generation.

FEATURES:
- PDF, JPG, PNG upload support
- UUID-based file naming
- Thumbnail generation for images
- File size validation (max 10MB for demo)

PRODUCTION UPGRADES:
- Use S3 for storage with presigned URLs
- Add virus scanning
- Implement CDN for thumbnails
- Add watermarking for sensitive documents
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime

from PIL import Image
from PyPDF2 import PdfReader


# Supported document types
SUPPORTED_EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png"
}

# File size limits
MAX_FILE_SIZE_MB = 10
THUMBNAIL_SIZE = (200, 200)


class DocumentProcessorService:
    """
    Handle document uploads, storage, and preprocessing.
    """
    
    def __init__(
        self,
        upload_dir: Optional[str] = None,
        thumbnail_dir: Optional[str] = None
    ):
        """
        Initialize the document processor.
        
        Args:
            upload_dir: Base directory for uploads
            thumbnail_dir: Directory for generated thumbnails
        """
        base_path = Path(__file__).parent.parent.parent / "data"
        self.upload_dir = Path(upload_dir or base_path / "uploads")
        self.thumbnail_dir = Path(thumbnail_dir or base_path / "thumbnails")
        
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_file(
        self,
        content_type: str,
        file_size: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate file type and size.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check content type
        if content_type not in SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file type: {content_type}. Supported: PDF, JPG, PNG"
        
        # Check file size
        file_size_mb = file_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            return False, f"File too large: {file_size_mb:.2f}MB (max: {MAX_FILE_SIZE_MB}MB)"
        
        return True, None
    
    def get_case_upload_dir(self, case_id: int) -> Path:
        """Get the upload directory for a specific case."""
        case_dir = self.upload_dir / f"case_{case_id}"
        case_dir.mkdir(parents=True, exist_ok=True)
        return case_dir
    
    async def save_document(
        self,
        content: bytes,
        case_id: int,
        content_type: str,
        original_filename: str
    ) -> Dict[str, Any]:
        """
        Save uploaded document with UUID naming.
        
        Args:
            content: File content bytes
            case_id: Associated case ID
            content_type: MIME type
            original_filename: Original filename
            
        Returns:
            Dict with file info
        """
        # Generate UUID filename
        file_uuid = str(uuid.uuid4())
        extension = SUPPORTED_EXTENSIONS.get(content_type, ".bin")
        new_filename = f"{file_uuid}{extension}"
        
        # Get case directory
        case_dir = self.get_case_upload_dir(case_id)
        file_path = case_dir / new_filename
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Generate thumbnail for images
        thumbnail_path = None
        if content_type.startswith("image/"):
            thumbnail_path = await self._generate_thumbnail(file_path, file_uuid)
        
        # Get file info
        file_info = {
            "file_uuid": file_uuid,
            "original_filename": original_filename,
            "stored_filename": new_filename,
            "file_path": str(file_path),
            "relative_path": f"case_{case_id}/{new_filename}",
            "content_type": content_type,
            "file_size": len(content),
            "thumbnail_path": str(thumbnail_path) if thumbnail_path else None,
            "uploaded_at": datetime.utcnow().isoformat()
        }
        
        return file_info
    
    async def _generate_thumbnail(
        self,
        image_path: Path,
        file_uuid: str
    ) -> Optional[Path]:
        """Generate thumbnail for an image."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                thumbnail_filename = f"{file_uuid}_thumb.jpg"
                thumbnail_path = self.thumbnail_dir / thumbnail_filename
                img.save(thumbnail_path, "JPEG", quality=85)
                
                return thumbnail_path
        except Exception as e:
            print(f"Thumbnail generation failed: {e}")
            return None
    
    def get_document_path(self, case_id: int, filename: str) -> Optional[Path]:
        """Get full path for a document."""
        file_path = self.upload_dir / f"case_{case_id}" / filename
        if file_path.exists():
            return file_path
        return None
    
    def list_case_documents(self, case_id: int) -> List[Dict[str, Any]]:
        """List all documents for a case."""
        case_dir = self.upload_dir / f"case_{case_id}"
        if not case_dir.exists():
            return []
        
        documents = []
        for file_path in case_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                documents.append({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "file_size": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return documents
    
    def extract_pdf_text(self, file_path: Path) -> Optional[str]:
        """Extract text from PDF using PyPDF2."""
        try:
            reader = PdfReader(str(file_path))
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n".join(text_parts)
        except Exception as e:
            print(f"PDF text extraction failed: {e}")
            return None
    
    def delete_document(self, case_id: int, filename: str) -> bool:
        """Delete a document and its thumbnail."""
        file_path = self.upload_dir / f"case_{case_id}" / filename
        
        if file_path.exists():
            # Delete main file
            file_path.unlink()
            
            # Try to delete thumbnail
            file_uuid = file_path.stem
            thumbnail_path = self.thumbnail_dir / f"{file_uuid}_thumb.jpg"
            if thumbnail_path.exists():
                thumbnail_path.unlink()
            
            return True
        return False


# Singleton instance
_processor: Optional[DocumentProcessorService] = None


def get_document_processor() -> DocumentProcessorService:
    """Get or create the document processor instance."""
    global _processor
    if _processor is None:
        _processor = DocumentProcessorService()
    return _processor
