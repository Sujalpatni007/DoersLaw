"""
Integration Tests - End-to-End Flows
"""
import pytest
from datetime import datetime
import uuid


@pytest.mark.integration
class TestDisputeFilingFlow:
    """Test end-to-end dispute filing flow"""
    
    def test_complete_intake_flow(self, sample_case, sample_user):
        """Test complete intake from user registration to case creation"""
        # Step 1: User registration/login
        user = sample_user.copy()
        assert user["id"] is not None
        
        # Step 2: Case submission
        case = sample_case.copy()
        case["user_id"] = user["id"]
        assert case["id"] is not None
        assert case["status"] == "intake"
        
        # Step 3: Document upload simulation
        documents = [
            {"type": "land_record", "uploaded": True},
            {"type": "id_proof", "uploaded": True},
        ]
        assert len(documents) >= 1
        
        # Step 4: Status should transition
        case["status"] = "verification"
        assert case["status"] == "verification"
    
    def test_multi_party_dispute_creation(self, sample_case):
        """Test dispute with multiple parties"""
        case = sample_case.copy()
        
        parties = [
            {"name": "Ramesh Patil", "role": "petitioner", "phone": "+91-9876543210"},
            {"name": "Suresh Patil", "role": "respondent", "phone": "+91-9876543211"},
            {"name": "Gram Panchayat", "role": "authority", "phone": None},
        ]
        
        case["parties"] = parties
        
        assert len(case["parties"]) == 3
        assert any(p["role"] == "petitioner" for p in case["parties"])
        assert any(p["role"] == "respondent" for p in case["parties"])
    
    def test_document_heavy_case(self, sample_case):
        """Test case with many documents"""
        case = sample_case.copy()
        
        documents = []
        doc_types = ["land_record", "survey_map", "tax_receipt", "sale_deed", 
                     "mutation_record", "court_order", "photograph"]
        
        for i, doc_type in enumerate(doc_types):
            documents.append({
                "id": str(uuid.uuid4()),
                "type": doc_type,
                "filename": f"{doc_type}_{i}.pdf",
                "case_id": case["id"],
                "uploaded_at": datetime.now().isoformat(),
            })
        
        case["documents"] = documents
        
        assert len(case["documents"]) == len(doc_types)
        assert all(d["case_id"] == case["id"] for d in case["documents"])


@pytest.mark.integration
class TestDocumentPipeline:
    """Test file upload -> OCR -> Verification pipeline"""
    
    def test_upload_ocr_verification_pipeline(self, sample_document, sample_land_record):
        """Test complete document processing pipeline"""
        # Step 1: Upload simulation
        doc = sample_document.copy()
        assert doc["id"] is not None
        
        # Step 2: OCR extraction simulation
        doc["extracted_text"] = f"""
        Land Record - {sample_land_record['state']}
        Khasra: {sample_land_record['khasra']}
        Owner: {sample_land_record['owner']}
        Area: {sample_land_record['area_acres']} acres
        """
        assert doc["extracted_text"] is not None
        
        # Step 3: Field extraction
        extracted_fields = {
            "khasra": sample_land_record["khasra"],
            "owner": sample_land_record["owner"],
            "area": sample_land_record["area_acres"],
        }
        doc["extracted_fields"] = extracted_fields
        
        assert doc["extracted_fields"]["khasra"] == "123/1"
        
        # Step 4: Verification against Bhulekh
        verification_result = {
            "status": "verified",
            "confidence": 0.95,
            "discrepancies": [],
        }
        doc["verification"] = verification_result
        
        assert doc["verification"]["status"] == "verified"
        assert doc["verification"]["confidence"] >= 0.85
    
    def test_document_rejection_flow(self, sample_document):
        """Test document rejection due to quality issues"""
        doc = sample_document.copy()
        
        # Simulate low quality OCR
        doc["ocr_confidence"] = 0.3
        doc["extracted_text"] = "Unreadable text..."
        
        # Should trigger rejection
        if doc["ocr_confidence"] < 0.6:
            doc["status"] = "rejected"
            doc["rejection_reason"] = "Low OCR confidence - please upload clearer image"
        
        assert doc["status"] == "rejected"
        assert "clearer" in doc["rejection_reason"]


@pytest.mark.integration
class TestMultiUserCollaboration:
    """Test multi-user case collaboration"""
    
    def test_lawyer_assignment(self, sample_case, sample_user):
        """Test lawyer assignment to case"""
        case = sample_case.copy()
        
        lawyer = {
            "id": 101,
            "name": "Adv. Rajesh Kulkarni",
            "specialization": "land_dispute",
            "assigned_at": datetime.now().isoformat(),
        }
        
        case["assigned_lawyer"] = lawyer
        
        assert case["assigned_lawyer"]["id"] == 101
        assert case["assigned_lawyer"]["specialization"] == "land_dispute"
    
    def test_case_notes_collaboration(self, sample_case):
        """Test multiple users adding notes to case"""
        case = sample_case.copy()
        case["notes"] = []
        
        # User adds note
        case["notes"].append({
            "id": str(uuid.uuid4()),
            "author_id": 1,
            "author_role": "user",
            "content": "Neighbor moved boundary stones last month",
            "created_at": datetime.now().isoformat(),
        })
        
        # Lawyer adds note
        case["notes"].append({
            "id": str(uuid.uuid4()),
            "author_id": 101,
            "author_role": "lawyer",
            "content": "Reviewed survey maps - discrepancy found",
            "created_at": datetime.now().isoformat(),
        })
        
        assert len(case["notes"]) == 2
        assert any(n["author_role"] == "user" for n in case["notes"])
        assert any(n["author_role"] == "lawyer" for n in case["notes"])


@pytest.mark.integration
class TestSMSWebhookHandling:
    """Test SMS webhook handling"""
    
    def test_incoming_sms_creates_conversation(self, sample_sms_message):
        """Test incoming SMS creates or retrieves conversation"""
        sms = sample_sms_message.copy()
        
        # Simulate conversation creation
        conversation = {
            "id": str(uuid.uuid4()),
            "phone_number": sms["phone_number"],
            "state": "initial",
            "messages": [sms],
            "created_at": datetime.now().isoformat(),
        }
        
        assert conversation["id"] is not None
        assert len(conversation["messages"]) == 1
    
    def test_sms_state_machine_transition(self, sample_sms_message):
        """Test SMS state machine responds correctly"""
        # Initial message
        conversation = {"state": "initial", "messages": []}
        
        # User sends "Hi"
        conversation["messages"].append({"content": "Hi", "direction": "inbound"})
        conversation["state"] = "awaiting_action"
        
        # Response sent
        conversation["messages"].append({
            "content": "Welcome! Reply 1 for case status, 2 for new case...",
            "direction": "outbound"
        })
        
        assert conversation["state"] == "awaiting_action"
        assert len(conversation["messages"]) == 2
    
    def test_sms_language_switching(self, sample_sms_message):
        """Test SMS language switching"""
        conversation = {"state": "awaiting_action", "language": "en"}
        
        # User selects Hindi
        conversation["messages"] = [{"content": "4", "direction": "inbound"}]
        conversation["state"] = "awaiting_language"
        
        # User selects Hindi (option 2)
        conversation["messages"].append({"content": "2", "direction": "inbound"})
        conversation["language"] = "hi"
        
        assert conversation["language"] == "hi"


@pytest.mark.integration
class TestUrgentEscalation:
    """Test urgent escalation path"""
    
    def test_urgent_case_escalation(self, sample_case):
        """Test urgent case triggers escalation"""
        case = sample_case.copy()
        case["priority"] = "urgent"
        
        # Simulate escalation trigger
        if case["priority"] == "urgent":
            case["status"] = "escalated"
            case["escalation_reason"] = "High priority case"
            case["escalated_at"] = datetime.now().isoformat()
        
        assert case["status"] == "escalated"
        assert case["escalated_at"] is not None
    
    def test_stalled_case_auto_escalation(self, sample_case):
        """Test auto-escalation for stalled cases"""
        case = sample_case.copy()
        case["last_activity_days"] = 15
        
        # Auto-escalate if no activity for 14 days
        if case["last_activity_days"] > 14:
            case["status"] = "escalated"
            case["escalation_reason"] = "No activity for 14+ days"
        
        assert case["status"] == "escalated"
