"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from datetime import datetime, timedelta
import random
import uuid


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_case():
    """Sample case data for testing"""
    return {
        "id": f"CASE-{datetime.now().year}-{random.randint(10000, 99999)}",
        "title": "Boundary Dispute - Test Village",
        "description": "Test case for boundary dispute between two farmers",
        "case_type": "boundary_dispute",
        "status": "intake",
        "created_at": datetime.now().isoformat(),
        "user_id": 1,
        "state": "Maharashtra",
        "district": "Pune",
        "village": "Lohegaon",
    }


@pytest.fixture
def sample_user():
    """Sample user data for testing"""
    return {
        "id": 1,
        "phone": "+91-9876543210",
        "name": "Test User",
        "email": "test@example.com",
        "role": "user",
        "language": "en",
    }


@pytest.fixture
def sample_document():
    """Sample document data for testing"""
    return {
        "id": str(uuid.uuid4()),
        "filename": "test_document.pdf",
        "file_type": "application/pdf",
        "size_bytes": 1024 * 100,
        "case_id": "CASE-2026-10001",
        "doc_type": "land_record",
        "extracted_text": "Sample extracted text from document",
    }


@pytest.fixture
def sample_land_record():
    """Sample land record for Bhulekh testing"""
    return {
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


@pytest.fixture
def sample_sms_message():
    """Sample SMS message for testing"""
    return {
        "phone_number": "+91-9876543210",
        "content": "Hi",
        "direction": "inbound",
    }


@pytest.fixture
def nlp_test_cases():
    """Test cases for NLP classification"""
    return [
        {"text": "My neighbor built a wall on my land", "expected": "boundary_dispute"},
        {"text": "I inherited land but my brother took it", "expected": "inheritance"},
        {"text": "Someone is farming on my property without permission", "expected": "encroachment"},
        {"text": "I bought land but registration not done", "expected": "ownership_dispute"},
        {"text": "Want to change land record name after father death", "expected": "mutation"},
        {"text": "Boundary wall needs to be moved 2 feet", "expected": "boundary_dispute"},
        {"text": "My uncle sold family ancestral property", "expected": "inheritance"},
        {"text": "Illegal construction on my vacant plot", "expected": "encroachment"},
    ]


@pytest.fixture
def village_scenarios():
    """Realistic village scenarios for testing"""
    return [
        {
            "name": "Two Brothers Land Split",
            "description": "After father's death, two brothers dispute inherited 5 acre land",
            "parties": ["Ramesh Singh", "Suresh Singh"],
            "case_type": "inheritance",
            "documents": ["death_certificate", "land_record", "will"],
        },
        {
            "name": "Neighboring Farm Boundary",
            "description": "Farmer claims neighbor moved boundary stones",
            "parties": ["Mohan Yadav", "Shyam Yadav"],
            "case_type": "boundary_dispute",
            "documents": ["survey_map", "land_record"],
        },
        {
            "name": "Illegal Construction",
            "description": "Someone built a shed on vacant plot during owner's absence",
            "parties": ["Priya Devi", "Unknown Encroacher"],
            "case_type": "encroachment",
            "documents": ["land_record", "photographs", "police_complaint"],
        },
    ]
