"""
DOER Platform - NLP API Router

Endpoints for dispute analysis, translation, and entity extraction.

ENDPOINTS:
- POST /api/v1/nlp/analyze-dispute - Full analysis pipeline
- POST /api/v1/nlp/translate - Translation only
- POST /api/v1/nlp/extract-entities - Entity extraction only
- POST /api/v1/nlp/transcribe - Voice-to-text

PRODUCTION UPGRADES:
- Add rate limiting per user
- Implement request queuing for heavy AI operations
- Add response caching with Redis
- Enable batch processing for multiple documents
"""

import os
import tempfile
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status

from app.nlp_schemas.nlp import (
    TranslateRequest, TranslateResponse,
    ClassifyRequest, ClassifyResponse, IntentScore,
    ExtractRequest, ExtractResponse,
    AnalyzeRequest, AnalyzeResponse,
    TranscribeResponse, FullTranscribeResponse
)
from app.nlp.translator import get_translation_service
from app.nlp.intent_classifier import get_intent_classifier
from app.nlp.entity_extractor import get_entity_extractor
from app.nlp.voice_processor import get_voice_processor, SUPPORTED_AUDIO_FORMATS, MAX_AUDIO_SIZE_MB


router = APIRouter(prefix="/nlp", tags=["NLP Analysis"])


@router.post("/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """
    Translate text between languages.
    
    Auto-detects source language if not specified.
    Supports: Hindi, Tamil, Telugu, English, and other Indian languages.
    """
    translator = get_translation_service()
    
    result = translator.translate(
        text=request.text,
        source_lang=request.source_language,
        target_lang=request.target_language
    )
    
    return TranslateResponse(
        original_text=result["original_text"],
        translated_text=result["translated_text"],
        source_language=result["source_language"],
        target_language=result["target_language"],
        confidence=result["confidence"],
        error=result.get("error")
    )


@router.post("/classify", response_model=ClassifyResponse)
async def classify_intent(request: ClassifyRequest):
    """
    Classify the dispute type from text.
    
    Categories:
    - ownership_dispute: Property ownership conflicts
    - boundary_dispute: Land boundary disagreements
    - inheritance_dispute: Inheritance-related conflicts
    - encroachment: Illegal occupation of land
    - title_issue: Title deed problems
    """
    translator = get_translation_service()
    classifier = get_intent_classifier()
    
    # Detect language
    detected_lang, lang_confidence = translator.detect_language(request.text)
    
    # Translate if needed
    if request.translate_first and detected_lang != "en":
        translation_result = translator.translate_to_english(request.text)
        processed_text = translation_result["translated_text"]
    else:
        processed_text = request.text
    
    # Classify
    classification = classifier.predict(processed_text)
    
    return ClassifyResponse(
        original_text=request.text,
        processed_text=processed_text,
        detected_language=detected_lang,
        intent=IntentScore(
            category=classification["category"],
            confidence=classification["confidence"],
            description=classification.get("description")
        ),
        all_scores=classification["all_scores"]
    )


@router.post("/extract-entities", response_model=ExtractResponse)
async def extract_entities(request: ExtractRequest):
    """
    Extract entities from text.
    
    Extracts:
    - Land area (acres, hectares, sq ft, etc.)
    - Survey/khasra numbers
    - Person names
    - Location names
    - Time references
    - Monetary amounts
    """
    translator = get_translation_service()
    extractor = get_entity_extractor()
    
    # Detect language
    detected_lang, _ = translator.detect_language(request.text)
    
    # Translate if needed
    if request.translate_first and detected_lang != "en":
        translation_result = translator.translate_to_english(request.text)
        processed_text = translation_result["translated_text"]
    else:
        processed_text = request.text
    
    # Extract entities
    entities = extractor.extract_all(processed_text)
    
    return ExtractResponse(
        original_text=request.text,
        processed_text=processed_text,
        detected_language=detected_lang,
        entities=entities
    )


@router.post("/analyze-dispute", response_model=AnalyzeResponse)
async def analyze_dispute(request: AnalyzeRequest):
    """
    Full dispute analysis pipeline.
    
    Performs:
    1. Language detection
    2. Translation to English
    3. Intent classification
    4. Entity extraction
    
    Returns comprehensive analysis with confidence scores.
    """
    translator = get_translation_service()
    classifier = get_intent_classifier()
    extractor = get_entity_extractor()
    
    # Step 1: Detect language
    detected_lang, lang_confidence = translator.detect_language(request.text)
    
    # Step 2: Translate to English
    if detected_lang != "en":
        translation_result = translator.translate_to_english(request.text)
        translated_text = translation_result["translated_text"]
        translation_confidence = translation_result["confidence"]
    else:
        translated_text = request.text
        translation_confidence = 1.0
    
    # Step 3: Classify intent
    classification = classifier.predict(translated_text)
    
    # Step 4: Extract entities
    entities = extractor.extract_all(translated_text)
    
    # Also extract from original text for better entity coverage
    original_entities = extractor.extract_all(request.text)
    
    # Merge entities (original + translated)
    for key in ["land_area", "survey_numbers", "monetary_amounts"]:
        if key in original_entities and original_entities[key]:
            # Add original entities not already present
            existing_values = {e.get("value") for e in entities.get(key, [])}
            for entity in original_entities[key]:
                if entity.get("value") not in existing_values:
                    entities.setdefault(key, []).append(entity)
    
    return AnalyzeResponse(
        original_text=request.text,
        detected_language=detected_lang,
        translated_text=translated_text,
        intent=IntentScore(
            category=classification["category"],
            confidence=classification["confidence"],
            description=classification.get("description")
        ),
        entities=entities,
        confidence_scores={
            "language_detection": lang_confidence,
            "translation": translation_confidence,
            "intent_classification": classification["confidence"],
            "overall": (lang_confidence + translation_confidence + classification["confidence"]) / 3
        }
    )


@router.post("/transcribe", response_model=FullTranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file (WAV, MP3, M4A, WEBM)"),
    language: Optional[str] = Form(None, description="Language hint (e.g., 'hi', 'en')"),
    analyze: bool = Form(True, description="Perform full analysis after transcription")
):
    """
    Transcribe audio to text and optionally analyze.
    
    Supports: WAV, MP3, M4A, WEBM, OGG
    Max file size: 25MB
    
    Uses OpenAI Whisper API. Requires OPENAI_API_KEY environment variable.
    """
    # Validate file type
    content_type = file.content_type or ""
    if content_type not in SUPPORTED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format: {content_type}. Supported: {list(SUPPORTED_AUDIO_FORMATS.keys())}"
        )
    
    # Check file size (read content)
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    
    if file_size_mb > MAX_AUDIO_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large: {file_size_mb:.2f}MB (max: {MAX_AUDIO_SIZE_MB}MB)"
        )
    
    # Save to temp file for processing
    suffix = SUPPORTED_AUDIO_FORMATS.get(content_type, ".wav")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        processor = get_voice_processor()
        
        # Transcribe
        transcription_result = await processor.transcribe(
            file_path=tmp_path,
            language=language,
            use_cache=True
        )
        
        transcription = TranscribeResponse(
            text=transcription_result.get("text", ""),
            cached=transcription_result.get("cached", False),
            language=language,
            error=transcription_result.get("error")
        )
        
        # Analyze if requested and transcription succeeded
        analysis = None
        if analyze and transcription.text and not transcription.error:
            analysis_request = AnalyzeRequest(text=transcription.text)
            analysis = await analyze_dispute(analysis_request)
        
        return FullTranscribeResponse(
            transcription=transcription,
            analysis=analysis
        )
        
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/languages")
async def get_supported_languages():
    """Get list of supported languages for translation."""
    from app.nlp.translator import SUPPORTED_LANGUAGES
    return {
        "languages": SUPPORTED_LANGUAGES,
        "default_target": "en"
    }


@router.get("/categories")
async def get_dispute_categories():
    """Get list of dispute categories for classification."""
    from app.nlp.training_data import INTENT_CATEGORIES
    return {
        "categories": INTENT_CATEGORIES
    }


@router.post("/train")
async def retrain_classifier():
    """
    Retrain the intent classifier.
    
    Note: This endpoint should be protected in production.
    """
    classifier = get_intent_classifier()
    metrics = classifier.train()
    
    return {
        "message": "Classifier retrained successfully",
        "metrics": metrics
    }
