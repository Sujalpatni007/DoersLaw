"""
DOER Platform - Entity Extraction Module

Extracts key entities from land dispute descriptions:
- Land area (acres, hectares, sq ft, etc.)
- Party names (persons involved)
- Locations (villages, districts, states)
- Time references (dates, durations)

Uses:
- Regex patterns for structured data (land area, dates)
- spaCy NER for names and locations

PRODUCTION UPGRADES:
- Train custom NER model on legal documents
- Add relationship extraction between entities
- Implement coreference resolution
- Add address parsing and geocoding
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class Entity:
    """Represents an extracted entity."""
    type: str
    value: str
    original: str
    start: int
    end: int
    confidence: float = 1.0


class EntityExtractor:
    """
    Extract entities from land dispute text.
    
    Combines regex patterns with optional spaCy NER.
    """
    
    def __init__(self, use_spacy: bool = True):
        """
        Initialize the entity extractor.
        
        Args:
            use_spacy: Whether to use spaCy for NER (requires model)
        """
        self.use_spacy = use_spacy
        self.nlp = None
        
        if use_spacy:
            try:
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Warning: spaCy model not found. Using regex-only extraction.")
                self.use_spacy = False
        
        # Compile regex patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for entity extraction."""
        
        # Land area patterns (English)
        self.area_patterns = [
            # Acres
            (r'(\d+(?:\.\d+)?)\s*(?:acre|acres|एकड़|ऎकड)', 'acres'),
            # Hectares
            (r'(\d+(?:\.\d+)?)\s*(?:hectare|hectares|हेक्टेयर)', 'hectares'),
            # Square feet
            (r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*ft\.?|square\s*feet|वर्ग\s*फीट)', 'sq_ft'),
            # Square meters
            (r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*m\.?|square\s*meters?|वर्ग\s*मीटर)', 'sq_m'),
            # Guntha (used in Maharashtra, Karnataka)
            (r'(\d+(?:\.\d+)?)\s*(?:guntha|gunta|गुंठा)', 'guntha'),
            # Bigha (used in UP, Bihar, Rajasthan)
            (r'(\d+(?:\.\d+)?)\s*(?:bigha|बीघा)', 'bigha'),
            # Katha (used in Bihar, Bengal)
            (r'(\d+(?:\.\d+)?)\s*(?:katha|kattha|कट्ठा)', 'katha'),
            # Cent (used in South India)
            (r'(\d+(?:\.\d+)?)\s*(?:cent|cents|सेंट)', 'cents'),
            # Generic area mention
            (r'(\d+(?:\.\d+)?)\s*(?:kanal|कनाल)', 'kanal'),
            (r'(\d+(?:\.\d+)?)\s*(?:marla|मर्ला)', 'marla'),
        ]
        
        # Survey number patterns
        self.survey_patterns = [
            r'(?:survey\s*(?:no\.?|number)?|सर्वे\s*नंबर)\s*[:\-]?\s*(\d+[/\-\w]*)',
            r'(?:s\.?\s*no\.?)\s*[:\-]?\s*(\d+[/\-\w]*)',
            r'(?:khasra\s*(?:no\.?|number)?|खसरा\s*नंबर?)\s*[:\-]?\s*(\d+[/\-\w]*)',
            r'(?:khata\s*(?:no\.?|number)?|खाता\s*नंबर?)\s*[:\-]?\s*(\d+[/\-\w]*)',
        ]
        
        # Time/duration patterns
        self.time_patterns = [
            # Years ago
            (r'(\d+)\s*(?:years?|साल|वर्ष)\s*(?:ago|पहले|पूर्व)?', 'years'),
            # Months ago
            (r'(\d+)\s*(?:months?|महीने?)\s*(?:ago|पहले)?', 'months'),
            # Year mentions
            (r'\b((?:19|20)\d{2})\b', 'year'),
            # Relative time
            (r'\b(last\s+(?:year|month|week)|पिछले\s+(?:साल|महीने))\b', 'relative'),
            (r'\b((?:5|10|15|20|25|30)\s+years?)\b', 'duration'),
        ]
        
        # Monetary amount patterns
        self.money_patterns = [
            (r'(?:rs\.?|₹|rupees?)\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:lakh|lac)?', 'INR'),
            (r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:lakh|lac)\s*(?:rs\.?|₹|rupees?)?', 'INR_lakh'),
            (r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:crore|cr)\s*(?:rs\.?|₹|rupees?)?', 'INR_crore'),
        ]
        
        # Compile all patterns
        self.compiled_area = [(re.compile(p, re.IGNORECASE), u) for p, u in self.area_patterns]
        self.compiled_survey = [re.compile(p, re.IGNORECASE) for p in self.survey_patterns]
        self.compiled_time = [(re.compile(p, re.IGNORECASE), t) for p, t in self.time_patterns]
        self.compiled_money = [(re.compile(p, re.IGNORECASE), c) for p, c in self.money_patterns]
    
    def extract_land_area(self, text: str) -> List[Dict[str, Any]]:
        """Extract land area mentions from text."""
        results = []
        
        for pattern, unit in self.compiled_area:
            for match in pattern.finditer(text):
                value = match.group(1).replace(',', '')
                results.append({
                    "value": float(value),
                    "unit": unit,
                    "original": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "normalized": f"{value} {unit}"
                })
        
        return results
    
    def extract_survey_numbers(self, text: str) -> List[Dict[str, Any]]:
        """Extract survey/khasra numbers from text."""
        results = []
        
        for pattern in self.compiled_survey:
            for match in pattern.finditer(text):
                results.append({
                    "value": match.group(1),
                    "original": match.group(0),
                    "start": match.start(),
                    "end": match.end()
                })
        
        return results
    
    def extract_time_references(self, text: str) -> List[Dict[str, Any]]:
        """Extract time/duration references from text."""
        results = []
        
        for pattern, time_type in self.compiled_time:
            for match in pattern.finditer(text):
                results.append({
                    "value": match.group(1),
                    "type": time_type,
                    "original": match.group(0),
                    "start": match.start(),
                    "end": match.end()
                })
        
        return results
    
    def extract_monetary_amounts(self, text: str) -> List[Dict[str, Any]]:
        """Extract monetary amounts from text."""
        results = []
        
        for pattern, currency in self.compiled_money:
            for match in pattern.finditer(text):
                value = match.group(1).replace(',', '')
                
                # Convert to base value
                if currency == 'INR_lakh':
                    normalized = float(value) * 100000
                elif currency == 'INR_crore':
                    normalized = float(value) * 10000000
                else:
                    normalized = float(value)
                
                results.append({
                    "value": normalized,
                    "original": match.group(0),
                    "type": "INR",
                    "start": match.start(),
                    "end": match.end()
                })
        
        return results
    
    def extract_names_and_locations(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract person names and locations using spaCy NER."""
        names = []
        locations = []
        organizations = []
        
        if self.nlp is None:
            return {
                "persons": names,
                "locations": locations,
                "organizations": organizations
            }
        
        doc = self.nlp(text)
        
        for ent in doc.ents:
            entity_info = {
                "value": ent.text,
                "start": ent.start_char,
                "end": ent.end_char,
                "label": ent.label_
            }
            
            if ent.label_ == "PERSON":
                names.append(entity_info)
            elif ent.label_ in ("GPE", "LOC", "FAC"):
                locations.append(entity_info)
            elif ent.label_ == "ORG":
                organizations.append(entity_info)
        
        return {
            "persons": names,
            "locations": locations,
            "organizations": organizations
        }
    
    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        Extract all entity types from text.
        
        Args:
            text: Input text (preferably in English)
            
        Returns:
            Dict with all extracted entities
        """
        ner_results = self.extract_names_and_locations(text)
        
        return {
            "land_area": self.extract_land_area(text),
            "survey_numbers": self.extract_survey_numbers(text),
            "time_references": self.extract_time_references(text),
            "monetary_amounts": self.extract_monetary_amounts(text),
            "persons": ner_results["persons"],
            "locations": ner_results["locations"],
            "organizations": ner_results["organizations"]
        }


# Singleton instance
_extractor: Optional[EntityExtractor] = None


def get_entity_extractor() -> EntityExtractor:
    """Get or create the entity extractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = EntityExtractor()
    return _extractor


def extract_entities(text: str) -> Dict[str, Any]:
    """
    Convenience function to extract all entities from text.
    
    Args:
        text: Input text
        
    Returns:
        Dict with extracted entities
    """
    extractor = get_entity_extractor()
    return extractor.extract_all(text)
