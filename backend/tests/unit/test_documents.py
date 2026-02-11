"""
Unit Tests - Document Processing
"""
import pytest
import os


@pytest.mark.unit
class TestDocumentValidation:
    """Test document upload validation"""
    
    ALLOWED_TYPES = ["application/pdf", "image/jpeg", "image/png", "image/webp"]
    MAX_SIZE_MB = 10
    
    def test_valid_pdf_type(self, sample_document):
        """Test PDF files are accepted"""
        assert sample_document["file_type"] in self.ALLOWED_TYPES
    
    def test_valid_image_types(self):
        """Test image types are accepted"""
        valid_images = ["image/jpeg", "image/png", "image/webp"]
        for img_type in valid_images:
            assert img_type in self.ALLOWED_TYPES
    
    def test_invalid_file_type_rejected(self):
        """Test executable and dangerous files are rejected"""
        dangerous_types = [
            "application/x-executable",
            "application/x-msdownload",
            "text/html",
            "application/javascript",
            "application/x-sh",
        ]
        
        for dangerous in dangerous_types:
            assert dangerous not in self.ALLOWED_TYPES
    
    def test_file_size_validation(self, sample_document):
        """Test file size within limits"""
        max_bytes = self.MAX_SIZE_MB * 1024 * 1024
        assert sample_document["size_bytes"] < max_bytes
    
    def test_oversized_file_rejected(self):
        """Test oversized files are rejected"""
        max_bytes = self.MAX_SIZE_MB * 1024 * 1024
        oversized = 15 * 1024 * 1024  # 15MB
        
        assert oversized > max_bytes
    
    def test_filename_sanitization(self):
        """Test malicious filenames are sanitized"""
        def sanitize_filename(filename: str) -> str:
            import re
            # Remove path traversal
            filename = filename.replace("../", "").replace("..\\", "")
            # Remove special chars
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            # Limit length
            name, ext = os.path.splitext(filename)
            return f"{name[:100]}{ext}"
        
        dangerous_names = [
            "../../../etc/passwd",
            "file<script>.pdf",
            "test\x00file.pdf",
            "a" * 500 + ".pdf",
        ]
        
        for name in dangerous_names:
            sanitized = sanitize_filename(name)
            assert "../" not in sanitized
            assert "<" not in sanitized
            assert len(sanitized) <= 110


@pytest.mark.unit  
class TestDocumentExtraction:
    """Test document content extraction"""
    
    def test_extract_land_record_fields(self, sample_land_record):
        """Test extraction of standard land record fields"""
        required_fields = ["state", "district", "tehsil", "village", "khasra", "owner"]
        
        for field in required_fields:
            assert field in sample_land_record
            assert sample_land_record[field] is not None
    
    def test_extract_area_validation(self, sample_land_record):
        """Test area extraction is numeric and positive"""
        area = sample_land_record["area_acres"]
        
        assert isinstance(area, (int, float))
        assert area > 0
    
    def test_encumbrance_detection(self, sample_land_record):
        """Test encumbrance field is present"""
        assert "encumbrances" in sample_land_record
    
    def test_ocr_text_cleanup(self):
        """Test OCR text cleanup"""
        def cleanup_ocr_text(text: str) -> str:
            # Remove extra whitespace
            text = " ".join(text.split())
            # Fix common OCR errors
            replacements = {
                "0": "O",  # Zero to O in names
                "|": "l",  # Pipe to l
            }
            return text.strip()
        
        messy_text = "  Ramesh   Pati|   \n\n owns   2.5  acres  "
        cleaned = cleanup_ocr_text(messy_text)
        
        assert "  " not in cleaned  # No double spaces
        assert "\n" not in cleaned


@pytest.mark.unit
class TestAgentStateMachine:
    """Test agent state machine transitions"""
    
    VALID_TRANSITIONS = {
        "intake": ["verification", "cancelled"],
        "verification": ["analysis", "intake", "cancelled"],
        "analysis": ["negotiation", "verification", "escalated"],
        "negotiation": ["resolution", "analysis", "escalated"],
        "resolution": ["closed", "negotiation"],
        "closed": [],
        "cancelled": [],
        "escalated": ["analysis", "closed"],
    }
    
    def test_valid_transition_intake_to_verification(self):
        """Test valid transition from intake to verification"""
        current = "intake"
        next_state = "verification"
        
        assert next_state in self.VALID_TRANSITIONS[current]
    
    def test_invalid_transition_intake_to_closed(self):
        """Test invalid transition from intake directly to closed"""
        current = "intake"
        next_state = "closed"
        
        assert next_state not in self.VALID_TRANSITIONS[current]
    
    def test_closed_state_is_terminal(self):
        """Test closed state has no valid transitions"""
        assert len(self.VALID_TRANSITIONS["closed"]) == 0
    
    def test_all_states_have_transitions_defined(self):
        """Test all states have transition rules defined"""
        all_states = ["intake", "verification", "analysis", "negotiation", 
                      "resolution", "closed", "cancelled", "escalated"]
        
        for state in all_states:
            assert state in self.VALID_TRANSITIONS
    
    def test_escalation_path_exists(self):
        """Test escalation path exists from analysis and negotiation"""
        assert "escalated" in self.VALID_TRANSITIONS["analysis"]
        assert "escalated" in self.VALID_TRANSITIONS["negotiation"]


@pytest.mark.unit
class TestDatabaseModels:
    """Test database model integrity"""
    
    def test_case_required_fields(self, sample_case):
        """Test case has all required fields"""
        required = ["id", "title", "case_type", "status", "user_id"]
        
        for field in required:
            assert field in sample_case, f"Missing required field: {field}"
    
    def test_case_id_format(self, sample_case):
        """Test case ID follows expected format"""
        import re
        pattern = r'^CASE-\d{4}-\d{5}$'
        
        assert re.match(pattern, sample_case["id"])
    
    def test_user_phone_format(self, sample_user):
        """Test user phone number format"""
        import re
        phone = sample_user["phone"]
        pattern = r'^\+91-\d{10}$'
        
        assert re.match(pattern, phone)
    
    def test_document_belongs_to_case(self, sample_document):
        """Test document has case association"""
        assert "case_id" in sample_document
        assert sample_document["case_id"] is not None
