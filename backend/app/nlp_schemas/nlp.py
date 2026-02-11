"""
DOER Platform - NLP Pydantic Schemas

Request and response schemas for NLP API endpoints.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ============================================================================
# Translation Schemas
# ============================================================================

class TranslateRequest(BaseModel):
    """Request for text translation."""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to translate")
    source_language: Optional[str] = Field(None, description="Source language code (auto-detect if None)")
    target_language: str = Field("en", description="Target language code")


class TranslateResponse(BaseModel):
    """Response from translation."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float = Field(..., ge=0, le=1)
    error: Optional[str] = None


# ============================================================================
# Intent Classification Schemas
# ============================================================================

class IntentScore(BaseModel):
    """Intent category with confidence score."""
    category: str
    confidence: float = Field(..., ge=0, le=1)
    description: Optional[str] = None


class ClassifyRequest(BaseModel):
    """Request for intent classification."""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to classify")
    translate_first: bool = Field(True, description="Translate to English before classification")


class ClassifyResponse(BaseModel):
    """Response from intent classification."""
    original_text: str
    processed_text: str
    detected_language: str
    intent: IntentScore
    all_scores: Dict[str, float]


# ============================================================================
# Entity Extraction Schemas
# ============================================================================

class LandAreaEntity(BaseModel):
    """Extracted land area entity."""
    value: float
    unit: str
    original: str
    normalized: str


class PersonEntity(BaseModel):
    """Extracted person name."""
    value: str
    start: int
    end: int


class LocationEntity(BaseModel):
    """Extracted location."""
    value: str
    start: int
    end: int
    label: str


class TimeEntity(BaseModel):
    """Extracted time reference."""
    value: str
    type: str
    original: str


class MoneyEntity(BaseModel):
    """Extracted monetary amount."""
    value: float
    type: str
    original: str


class ExtractRequest(BaseModel):
    """Request for entity extraction."""
    text: str = Field(..., min_length=1, max_length=10000)
    translate_first: bool = Field(True, description="Translate to English before extraction")


class ExtractResponse(BaseModel):
    """Response from entity extraction."""
    original_text: str
    processed_text: str
    detected_language: str
    entities: Dict[str, List[Any]] = Field(
        default_factory=dict,
        description="Extracted entities by type"
    )


# ============================================================================
# Full Analysis Schemas
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request for full dispute analysis."""
    text: str = Field(..., min_length=1, max_length=10000, description="Dispute description")


class AnalyzeResponse(BaseModel):
    """Full analysis response."""
    original_text: str
    detected_language: str
    translated_text: str
    intent: IntentScore
    entities: Dict[str, List[Any]]
    confidence_scores: Dict[str, float]


# ============================================================================
# Voice Transcription Schemas
# ============================================================================

class TranscribeResponse(BaseModel):
    """Response from audio transcription."""
    text: str
    cached: bool
    language: Optional[str] = None
    error: Optional[str] = None


class FullTranscribeResponse(BaseModel):
    """Full response including analysis of transcribed text."""
    transcription: TranscribeResponse
    analysis: Optional[AnalyzeResponse] = None
