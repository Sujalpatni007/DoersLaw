"""
DOER Platform - OCR Engine Service

Extracts text from documents using OCR.

ENGINES:
- Primary: Tesseract OCR (good for English)
- Fallback: EasyOCR (better for Hindi/regional languages)

EXTRACTS:
- Khasra/survey numbers
- Owner names
- Land area measurements
- Village/district information

PRODUCTION UPGRADES:
- Use Google Vision API for higher accuracy
- Implement document classification
- Add table extraction
- Integrate with layout analysis
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class ExtractedLandData:
    """Structured land document data."""
    khasra_numbers: List[str]
    survey_numbers: List[str]
    owner_names: List[str]
    area_measurements: List[Dict[str, Any]]
    village: Optional[str]
    district: Optional[str]
    state: Optional[str]
    raw_text: str


class OCREngine:
    """
    OCR text extraction from documents and images.
    """
    
    def __init__(self, use_easyocr: bool = True):
        """
        Initialize OCR engine.
        
        Args:
            use_easyocr: Whether to use EasyOCR as fallback
        """
        self.use_easyocr = use_easyocr
        self._tesseract_available = self._check_tesseract()
        self._easyocr_reader = None
        
        # Compile extraction patterns
        self._compile_patterns()
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available."""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            print("Warning: Tesseract not available. Install with: brew install tesseract")
            return False
    
    def _get_easyocr_reader(self):
        """Lazy-load EasyOCR reader."""
        if self._easyocr_reader is None and self.use_easyocr:
            try:
                import easyocr
                # Support English and Hindi
                self._easyocr_reader = easyocr.Reader(['en', 'hi'], gpu=False)
            except Exception as e:
                print(f"EasyOCR initialization failed: {e}")
        return self._easyocr_reader
    
    def _compile_patterns(self):
        """Compile regex patterns for data extraction."""
        
        # Khasra number patterns
        self.khasra_pattern = re.compile(
            r'(?:khasra|खसरा|ख\.?\s*सं\.?)\s*(?:no\.?|नं\.?|number)?\s*[:\-]?\s*(\d+[/\-\w]*)',
            re.IGNORECASE
        )
        
        # Survey number patterns
        self.survey_pattern = re.compile(
            r'(?:survey|सर्वे|s\.?\s*no\.?)\s*(?:no\.?|number)?\s*[:\-]?\s*(\d+[/\-\w]*)',
            re.IGNORECASE
        )
        
        # Area patterns
        self.area_patterns = [
            (re.compile(r'(\d+(?:\.\d+)?)\s*(?:acre|acres|एकड़)', re.IGNORECASE), 'acres'),
            (re.compile(r'(\d+(?:\.\d+)?)\s*(?:hectare|hectares|हेक्टेयर)', re.IGNORECASE), 'hectares'),
            (re.compile(r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*ft|square\s*feet|वर्ग\s*फीट)', re.IGNORECASE), 'sq_ft'),
            (re.compile(r'(\d+(?:\.\d+)?)\s*(?:bigha|बीघा)', re.IGNORECASE), 'bigha'),
            (re.compile(r'(\d+(?:\.\d+)?)\s*(?:guntha|गुंठा)', re.IGNORECASE), 'guntha'),
        ]
        
        # Name patterns (simple heuristic)
        self.name_patterns = [
            re.compile(r'(?:name|नाम|owner|मालिक|proprietor)\s*[:\-]?\s*([A-Za-z\s]+|[\u0900-\u097F\s]+)', re.IGNORECASE),
            re.compile(r'(?:s/o|d/o|w/o|पुत्र|पुत्री)\s*[:\-]?\s*([A-Za-z\s]+|[\u0900-\u097F\s]+)', re.IGNORECASE),
        ]
        
        # Location patterns
        self.village_pattern = re.compile(
            r'(?:village|गांव|ग्राम)\s*[:\-]?\s*([A-Za-z\s]+|[\u0900-\u097F\s]+)',
            re.IGNORECASE
        )
        self.district_pattern = re.compile(
            r'(?:district|जिला)\s*[:\-]?\s*([A-Za-z\s]+|[\u0900-\u097F\s]+)',
            re.IGNORECASE
        )
        self.state_pattern = re.compile(
            r'(?:state|राज्य)\s*[:\-]?\s*([A-Za-z\s]+|[\u0900-\u097F\s]+)',
            re.IGNORECASE
        )
    
    def extract_text_tesseract(self, image_path: Path, lang: str = 'eng+hin') -> Optional[str]:
        """Extract text using Tesseract OCR."""
        if not self._tesseract_available:
            return None
        
        try:
            import pytesseract
            from PIL import Image
            
            with Image.open(image_path) as img:
                # Preprocess: convert to grayscale
                if img.mode != 'L':
                    img = img.convert('L')
                
                # Extract text
                text = pytesseract.image_to_string(img, lang=lang)
                return text.strip()
        except Exception as e:
            print(f"Tesseract OCR failed: {e}")
            return None
    
    def extract_text_easyocr(self, image_path: Path) -> Optional[str]:
        """Extract text using EasyOCR."""
        reader = self._get_easyocr_reader()
        if reader is None:
            return None
        
        try:
            results = reader.readtext(str(image_path))
            # Combine all detected text
            text_parts = [result[1] for result in results]
            return "\n".join(text_parts)
        except Exception as e:
            print(f"EasyOCR failed: {e}")
            return None
    
    def extract_text(self, file_path: Path) -> Optional[str]:
        """
        Extract text from image using available OCR engines.
        
        Tries Tesseract first, falls back to EasyOCR.
        """
        # Try Tesseract first
        text = self.extract_text_tesseract(file_path)
        
        # Fallback to EasyOCR if Tesseract fails or returns empty
        if not text and self.use_easyocr:
            text = self.extract_text_easyocr(file_path)
        
        return text
    
    def extract_structured_data(self, text: str) -> ExtractedLandData:
        """
        Extract structured land record data from OCR text.
        
        Args:
            text: Raw OCR text
            
        Returns:
            ExtractedLandData with parsed fields
        """
        # Extract khasra numbers
        khasra_matches = self.khasra_pattern.findall(text)
        khasra_numbers = list(set(khasra_matches))
        
        # Extract survey numbers
        survey_matches = self.survey_pattern.findall(text)
        survey_numbers = list(set(survey_matches))
        
        # Extract area measurements
        area_measurements = []
        for pattern, unit in self.area_patterns:
            for match in pattern.finditer(text):
                value = match.group(1).replace(',', '')
                area_measurements.append({
                    "value": float(value),
                    "unit": unit,
                    "original": match.group(0)
                })
        
        # Extract owner names
        owner_names = []
        for pattern in self.name_patterns:
            for match in pattern.finditer(text):
                name = match.group(1).strip()
                if len(name) > 2:  # Filter short matches
                    owner_names.append(name)
        owner_names = list(set(owner_names))
        
        # Extract locations
        village_match = self.village_pattern.search(text)
        district_match = self.district_pattern.search(text)
        state_match = self.state_pattern.search(text)
        
        return ExtractedLandData(
            khasra_numbers=khasra_numbers,
            survey_numbers=survey_numbers,
            owner_names=owner_names,
            area_measurements=area_measurements,
            village=village_match.group(1).strip() if village_match else None,
            district=district_match.group(1).strip() if district_match else None,
            state=state_match.group(1).strip() if state_match else None,
            raw_text=text
        )
    
    async def process_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Full document processing pipeline.
        
        Args:
            file_path: Path to document/image
            
        Returns:
            Dict with extracted text and structured data
        """
        suffix = file_path.suffix.lower()
        
        # For PDFs, we'd need to convert to images first
        if suffix == '.pdf':
            # Try PyPDF2 text extraction first
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(str(file_path))
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                text = "\n".join(text_parts)
            except Exception as e:
                print(f"PDF extraction failed: {e}")
                text = None
                
            # If no text extracted and pdf2image available, try OCR
            if not text:
                try:
                    from pdf2image import convert_from_path
                    images = convert_from_path(str(file_path), first_page=1, last_page=1)
                    if images:
                        # Save temp image
                        temp_path = file_path.with_suffix('.png')
                        images[0].save(temp_path)
                        text = self.extract_text(temp_path)
                        temp_path.unlink()  # Clean up
                except Exception as e:
                    print(f"PDF to image conversion failed: {e}")
                    text = None
        else:
            # Image files
            text = self.extract_text(file_path)
        
        if not text:
            return {
                "success": False,
                "error": "Could not extract text from document",
                "raw_text": None,
                "extracted_data": None
            }
        
        # Extract structured data
        extracted = self.extract_structured_data(text)
        
        return {
            "success": True,
            "raw_text": extracted.raw_text,
            "extracted_data": {
                "khasra_numbers": extracted.khasra_numbers,
                "survey_numbers": extracted.survey_numbers,
                "owner_names": extracted.owner_names,
                "area_measurements": extracted.area_measurements,
                "village": extracted.village,
                "district": extracted.district,
                "state": extracted.state
            }
        }


# Singleton instance
_engine: Optional[OCREngine] = None


def get_ocr_engine() -> OCREngine:
    """Get or create the OCR engine instance."""
    global _engine
    if _engine is None:
        _engine = OCREngine()
    return _engine
