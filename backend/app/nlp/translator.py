"""
DOER Platform - Language Detection & Translation Module

Uses deep-translator for multi-language translation support.
Currently supports: Hindi (hi), Tamil (ta), Telugu (te), English (en)

PRODUCTION UPGRADES:
- Use Google Cloud Translation API for higher reliability
- Implement response caching with Redis
- Add batch translation for efficiency
- Consider AWS Translate or Azure Translator for enterprise
"""

from typing import Optional, Dict, Tuple
from deep_translator import GoogleTranslator
from deep_translator.exceptions import (
    LanguageNotSupportedException,
    TranslationNotFound,
    RequestError
)
import re


# Supported languages for land dispute resolution
SUPPORTED_LANGUAGES = {
    "en": "english",
    "hi": "hindi", 
    "ta": "tamil",
    "te": "telugu",
    "kn": "kannada",
    "mr": "marathi",
    "gu": "gujarati",
    "bn": "bengali",
    "pa": "punjabi"
}

# Language detection patterns
HINDI_PATTERN = re.compile(r'[\u0900-\u097F]')  # Devanagari script
TAMIL_PATTERN = re.compile(r'[\u0B80-\u0BFF]')  # Tamil script
TELUGU_PATTERN = re.compile(r'[\u0C00-\u0C7F]')  # Telugu script
KANNADA_PATTERN = re.compile(r'[\u0C80-\u0CFF]')  # Kannada script
MARATHI_PATTERN = re.compile(r'[\u0900-\u097F]')  # Uses Devanagari
GUJARATI_PATTERN = re.compile(r'[\u0A80-\u0AFF]')  # Gujarati script
BENGALI_PATTERN = re.compile(r'[\u0980-\u09FF]')  # Bengali script
PUNJABI_PATTERN = re.compile(r'[\u0A00-\u0A7F]')  # Gurmukhi script


class TranslationService:
    """
    Multi-language translation service for legal document analysis.
    
    Automatically detects input language and translates to English
    for NLP processing, then can translate responses back.
    """
    
    def __init__(self):
        self._translators: Dict[str, GoogleTranslator] = {}
    
    def _get_translator(self, source: str, target: str) -> GoogleTranslator:
        """Get or create a translator instance."""
        key = f"{source}_{target}"
        if key not in self._translators:
            self._translators[key] = GoogleTranslator(source=source, target=target)
        return self._translators[key]
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of input text using script patterns.
        
        Returns:
            Tuple of (language_code, confidence_score)
            
        Note: This is a rule-based detection. For production, consider
        using langdetect or Google's language detection API.
        """
        if not text or not text.strip():
            return ("en", 0.0)
        
        text_clean = text.strip()
        total_chars = len(text_clean)
        
        # Count characters in each script
        hindi_chars = len(HINDI_PATTERN.findall(text_clean))
        tamil_chars = len(TAMIL_PATTERN.findall(text_clean))
        telugu_chars = len(TELUGU_PATTERN.findall(text_clean))
        kannada_chars = len(KANNADA_PATTERN.findall(text_clean))
        gujarati_chars = len(GUJARATI_PATTERN.findall(text_clean))
        bengali_chars = len(BENGALI_PATTERN.findall(text_clean))
        punjabi_chars = len(PUNJABI_PATTERN.findall(text_clean))
        
        # Determine dominant script
        script_counts = {
            "hi": hindi_chars,  # Devanagari could be Hindi or Marathi
            "ta": tamil_chars,
            "te": telugu_chars,
            "kn": kannada_chars,
            "gu": gujarati_chars,
            "bn": bengali_chars,
            "pa": punjabi_chars
        }
        
        max_script = max(script_counts, key=script_counts.get)
        max_count = script_counts[max_script]
        
        if max_count > 0:
            confidence = min(max_count / (total_chars * 0.5), 1.0)
            return (max_script, confidence)
        
        # Default to English if no Indic script detected
        return ("en", 0.8)
    
    def translate(
        self, 
        text: str, 
        source_lang: Optional[str] = None,
        target_lang: str = "en"
    ) -> Dict[str, any]:
        """
        Translate text to the target language.
        
        Args:
            text: Text to translate
            source_lang: Source language code (auto-detect if None)
            target_lang: Target language code (default: English)
            
        Returns:
            Dict with translated_text, source_lang, target_lang, confidence
        """
        if not text or not text.strip():
            return {
                "translated_text": "",
                "source_language": "unknown",
                "target_language": target_lang,
                "confidence": 0.0,
                "original_text": text
            }
        
        # Detect source language if not provided
        if source_lang is None:
            source_lang, confidence = self.detect_language(text)
        else:
            confidence = 1.0
        
        # If source and target are the same, no translation needed
        if source_lang == target_lang:
            return {
                "translated_text": text,
                "source_language": source_lang,
                "target_language": target_lang,
                "confidence": confidence,
                "original_text": text
            }
        
        try:
            # Handle 'auto' detection for Google Translator
            translator = self._get_translator(
                source=source_lang if source_lang != "en" else "auto",
                target=target_lang
            )
            translated = translator.translate(text)
            
            return {
                "translated_text": translated,
                "source_language": source_lang,
                "target_language": target_lang,
                "confidence": confidence,
                "original_text": text
            }
            
        except LanguageNotSupportedException as e:
            return {
                "translated_text": text,
                "source_language": source_lang,
                "target_language": target_lang,
                "confidence": 0.0,
                "error": f"Language not supported: {str(e)}",
                "original_text": text
            }
        except (TranslationNotFound, RequestError) as e:
            return {
                "translated_text": text,
                "source_language": source_lang,
                "target_language": target_lang,
                "confidence": 0.0,
                "error": f"Translation failed: {str(e)}",
                "original_text": text
            }
        except Exception as e:
            # Fallback for any other errors
            return {
                "translated_text": text,
                "source_language": source_lang,
                "target_language": target_lang,
                "confidence": 0.0,
                "error": f"Unexpected error: {str(e)}",
                "original_text": text
            }
    
    def translate_to_english(self, text: str) -> Dict[str, any]:
        """Convenience method to translate any text to English."""
        return self.translate(text, target_lang="en")
    
    def translate_from_english(self, text: str, target_lang: str) -> Dict[str, any]:
        """Translate English text to target language."""
        return self.translate(text, source_lang="en", target_lang=target_lang)


# Singleton instance
_translator: Optional[TranslationService] = None


def get_translation_service() -> TranslationService:
    """Get or create the translation service instance."""
    global _translator
    if _translator is None:
        _translator = TranslationService()
    return _translator
