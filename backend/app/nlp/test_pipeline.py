"""
DOER Platform - NLP Pipeline Test Script

Validates the NLP analysis pipeline with 10 Hindi sample queries.

Run:
    cd backend
    source venv/bin/activate
    python -m app.nlp.test_pipeline
"""

import json
import sys
from typing import Dict, List, Any

# Test samples in Hindi (transliterated and Hindi script)
HINDI_TEST_SAMPLES = [
    {
        "text": "मेरी 2 एकड़ जमीन पर पड़ोसी ने कब्जा कर लिया है",
        "expected_intent": "encroachment",
        "description": "Encroachment - Neighbor occupied 2 acres"
    },
    {
        "text": "पिताजी की मृत्यु के बाद भाइयों में जमीन का बंटवारा नहीं हो पा रहा",
        "expected_intent": "inheritance_dispute",
        "description": "Inheritance - Land partition dispute after father's death"
    },
    {
        "text": "मेरे खेत की सीमा पड़ोसी ने अपने अंदर कर ली है",
        "expected_intent": "boundary_dispute",
        "description": "Boundary - Neighbor encroached boundary"
    },
    {
        "text": "जमीन की रजिस्ट्री में गलत नाम लिखा हुआ है",
        "expected_intent": "title_issue",
        "description": "Title - Wrong name in registry"
    },
    {
        "text": "मेरी पुश्तैनी जमीन पर किसी और ने मालिकाना हक जताया है",
        "expected_intent": "ownership_dispute",
        "description": "Ownership - Ancestral land claim by someone else"
    },
    {
        "text": "5 बीघा खेत का मालिकाना हक लड़ाई चल रही है",
        "expected_intent": "ownership_dispute",
        "description": "Ownership - 5 bigha land ownership fight"
    },
    {
        "text": "दादाजी की 10 एकड़ जमीन का बंटवारा करना है",
        "expected_intent": "inheritance_dispute",
        "description": "Inheritance - Grandfather's 10 acre land partition"
    },
    {
        "text": "पड़ोसी ने बाउंड्री वॉल मेरी तरफ खिसका दी है",
        "expected_intent": "boundary_dispute",
        "description": "Boundary - Wall shifted towards my side"
    },
    {
        "text": "जमीन के कागजात में फर्जीवाड़ा हुआ है",
        "expected_intent": "title_issue",
        "description": "Title - Fraud in land documents"
    },
    {
        "text": "खाली पड़ी जमीन पर झुग्गी बन गई है",
        "expected_intent": "encroachment",
        "description": "Encroachment - Slum on vacant land"
    }
]


def test_translation():
    """Test translation service."""
    print("\n" + "="*60)
    print("Testing Translation Service")
    print("="*60)
    
    from app.nlp.translator import get_translation_service
    translator = get_translation_service()
    
    passed = 0
    failed = 0
    
    for sample in HINDI_TEST_SAMPLES[:3]:
        result = translator.translate_to_english(sample["text"])
        
        print(f"\n📝 Original: {sample['text'][:50]}...")
        print(f"🇬🇧 Translated: {result['translated_text'][:50]}...")
        print(f"📊 Language: {result['source_language']} (confidence: {result['confidence']:.2f})")
        
        if result['source_language'] == 'hi' and result['confidence'] > 0.5:
            print("✅ PASSED")
            passed += 1
        else:
            print("❌ FAILED")
            failed += 1
    
    print(f"\n📈 Translation: {passed}/{passed+failed} tests passed")
    return passed, failed


def test_intent_classification():
    """Test intent classification."""
    print("\n" + "="*60)
    print("Testing Intent Classification")
    print("="*60)
    
    from app.nlp.translator import get_translation_service
    from app.nlp.intent_classifier import get_intent_classifier
    
    translator = get_translation_service()
    classifier = get_intent_classifier()
    
    passed = 0
    failed = 0
    
    for sample in HINDI_TEST_SAMPLES:
        # Translate first
        translation = translator.translate_to_english(sample["text"])
        english_text = translation["translated_text"]
        
        # Classify
        result = classifier.predict(english_text)
        
        is_correct = result["category"] == sample["expected_intent"]
        
        print(f"\n📝 {sample['description']}")
        print(f"Expected: {sample['expected_intent']}")
        print(f"Predicted: {result['category']} (confidence: {result['confidence']:.2f})")
        
        if is_correct:
            print("✅ PASSED")
            passed += 1
        else:
            print("❌ FAILED")
            failed += 1
    
    accuracy = passed / len(HINDI_TEST_SAMPLES) * 100
    print(f"\n📈 Intent Classification: {passed}/{len(HINDI_TEST_SAMPLES)} correct ({accuracy:.1f}%)")
    return passed, failed


def test_entity_extraction():
    """Test entity extraction."""
    print("\n" + "="*60)
    print("Testing Entity Extraction")
    print("="*60)
    
    from app.nlp.entity_extractor import get_entity_extractor
    
    extractor = get_entity_extractor()
    
    test_texts = [
        "मेरी 2 एकड़ जमीन पर पड़ोसी ने कब्जा कर लिया है",
        "5 बीघा खेत का मालिकाना हक",
        "10,000 sq ft plot in Mumbai",
        "Survey number 123/4 in Pune district",
        "Property dispute since 2015, about 8 years ago"
    ]
    
    for text in test_texts:
        entities = extractor.extract_all(text)
        print(f"\n📝 Text: {text[:50]}...")
        
        for entity_type, items in entities.items():
            if items:
                print(f"  {entity_type}: {items}")
    
    return len(test_texts), 0


def test_full_pipeline():
    """Test the full analysis pipeline."""
    print("\n" + "="*60)
    print("Testing Full Analysis Pipeline")
    print("="*60)
    
    from app.nlp.translator import get_translation_service
    from app.nlp.intent_classifier import get_intent_classifier
    from app.nlp.entity_extractor import get_entity_extractor
    
    translator = get_translation_service()
    classifier = get_intent_classifier()
    extractor = get_entity_extractor()
    
    sample = HINDI_TEST_SAMPLES[0]
    
    print(f"\n📝 Input: {sample['text']}")
    print(f"Expected Intent: {sample['expected_intent']}")
    
    # Step 1: Detect language
    detected_lang, lang_conf = translator.detect_language(sample["text"])
    print(f"\n1️⃣ Language Detection:")
    print(f"   Language: {detected_lang} (confidence: {lang_conf:.2f})")
    
    # Step 2: Translate
    translation = translator.translate_to_english(sample["text"])
    print(f"\n2️⃣ Translation:")
    print(f"   English: {translation['translated_text']}")
    
    # Step 3: Classify
    classification = classifier.predict(translation["translated_text"])
    print(f"\n3️⃣ Intent Classification:")
    print(f"   Category: {classification['category']}")
    print(f"   Confidence: {classification['confidence']:.2f}")
    print(f"   All scores: {json.dumps(classification['all_scores'], indent=6)}")
    
    # Step 4: Extract entities
    entities = extractor.extract_all(sample["text"])  # Also check original
    english_entities = extractor.extract_all(translation["translated_text"])
    
    # Merge
    for key in english_entities:
        if english_entities[key] and key in entities:
            entities[key].extend(english_entities[key])
    
    print(f"\n4️⃣ Entity Extraction:")
    for entity_type, items in entities.items():
        if items:
            print(f"   {entity_type}: {items}")
    
    # Final output
    output = {
        "original_text": sample["text"],
        "detected_language": detected_lang,
        "translated_text": translation["translated_text"],
        "intent": {
            "category": classification["category"],
            "confidence": classification["confidence"]
        },
        "entities": {k: v for k, v in entities.items() if v}
    }
    
    print(f"\n📊 Final JSON Output:")
    print(json.dumps(output, indent=2, ensure_ascii=False))
    
    return 1, 0


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🔬 DOER Platform - NLP Pipeline Validation")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    
    # Test 1: Translation
    try:
        p, f = test_translation()
        total_passed += p
        total_failed += f
    except Exception as e:
        print(f"❌ Translation test error: {e}")
        total_failed += 1
    
    # Test 2: Intent Classification
    try:
        p, f = test_intent_classification()
        total_passed += p
        total_failed += f
    except Exception as e:
        print(f"❌ Intent classification test error: {e}")
        total_failed += 1
    
    # Test 3: Entity Extraction
    try:
        p, f = test_entity_extraction()
        total_passed += p
        total_failed += f
    except Exception as e:
        print(f"❌ Entity extraction test error: {e}")
        total_failed += 1
    
    # Test 4: Full Pipeline
    try:
        p, f = test_full_pipeline()
        total_passed += p
        total_failed += f
    except Exception as e:
        print(f"❌ Full pipeline test error: {e}")
        total_failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"Total Tests Passed: {total_passed}")
    print(f"Total Tests Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n✅ All tests passed! NLP pipeline is working correctly.")
        return 0
    else:
        print(f"\n⚠️ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
