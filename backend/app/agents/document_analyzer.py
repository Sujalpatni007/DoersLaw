"""
DOER Platform - Document Analyzer Agent

AI-powered document analysis for land dispute cases.
Uses Ollama (local) or OpenAI (cloud) for document summarization and extraction.

ARCHITECTURE:
This module provides an abstraction layer over different AI providers:
1. Ollama (default): Free, runs locally on your laptop
2. OpenAI: Cloud-based, requires API key and billing

SETUP OLLAMA (LOCAL - FREE):
1. Install Ollama: https://ollama.ai/download
2. Pull the model: ollama pull llama3.2
3. Start Ollama server: ollama serve (usually auto-starts)
4. The API runs on http://localhost:11434

PRODUCTION UPGRADE TO OPENAI:
1. Set AI_PROVIDER="openai" in .env
2. Set OPENAI_API_KEY="your-key" in .env
3. Optionally adjust OPENAI_RATE_LIMIT_RPM

FUTURE ENHANCEMENTS:
- Add OCR with Tesseract for image-based documents
- Fine-tune models on legal document datasets
- Add document classification (deed, survey, court order, etc.)
- Implement RAG for case-specific context
- Add entity extraction (names, dates, land measurements)
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import httpx

from app.config import get_settings

settings = get_settings()


class DocumentAnalyzer:
    """
    AI-powered document analyzer for legal documents.
    
    Provides document summarization, key information extraction,
    and case recommendations based on uploaded documents.
    """
    
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.client = httpx.AsyncClient(timeout=120.0)
        
        # Rate limiting state for OpenAI
        self._request_times: list = []
        self._rate_limit = settings.OPENAI_RATE_LIMIT_RPM
    
    async def _check_rate_limit(self) -> None:
        """
        Simple rate limiting for OpenAI API.
        
        PRODUCTION: Use Redis-based distributed rate limiting:
        ```python
        key = f"openai_ratelimit:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)
        if count > self._rate_limit:
            raise RateLimitExceeded()
        ```
        """
        if self.provider != "openai":
            return
        
        now = datetime.utcnow().timestamp()
        # Remove requests older than 1 minute
        self._request_times = [t for t in self._request_times if now - t < 60]
        
        if len(self._request_times) >= self._rate_limit:
            wait_time = 60 - (now - self._request_times[0])
            await asyncio.sleep(wait_time)
        
        self._request_times.append(now)
    
    async def _call_ollama(self, prompt: str, system: str = "") -> str:
        """
        Call Ollama API for local inference.
        
        Ollama provides a REST API compatible with the chat completion format.
        """
        try:
            response = await self.client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower for more factual responses
                        "top_p": 0.9,
                        "num_ctx": 4096  # Context window
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except httpx.HTTPError as e:
            # Ollama not running or model not available
            return f"Error: Could not connect to Ollama. Make sure Ollama is running. ({str(e)})"
    
    async def _call_openai(self, prompt: str, system: str = "") -> str:
        """
        Call OpenAI API for cloud inference.
        
        PRODUCTION: Add retry logic with exponential backoff
        """
        if not settings.OPENAI_API_KEY:
            return "Error: OpenAI API key not configured"
        
        await self._check_rate_limit()
        
        try:
            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": system} if system else {},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            return f"Error calling OpenAI: {str(e)}"
    
    async def _generate(self, prompt: str, system: str = "") -> str:
        """Route request to appropriate AI provider."""
        if self.provider == "openai":
            return await self._call_openai(prompt, system)
        else:
            return await self._call_ollama(prompt, system)
    
    async def summarize_document(
        self, 
        text: str, 
        document_type: str = "legal document"
    ) -> Dict[str, Any]:
        """
        Generate a summary of a legal document.
        
        Args:
            text: Extracted text from the document
            document_type: Type of document for context
            
        Returns:
            Dict containing summary and key points
        """
        system_prompt = """You are a legal document analyst specializing in land disputes in India. 
Your task is to summarize legal documents accurately and identify key information.
Always be factual and cite specific details from the document.
If information is unclear or missing, explicitly state that."""
        
        prompt = f"""Please analyze this {document_type} and provide:

1. A brief summary (2-3 sentences)
2. Key parties involved
3. Important dates mentioned
4. Land details (location, area, survey numbers)
5. Any legal claims or disputes mentioned
6. Critical observations or potential issues

Document text:
---
{text[:4000]}  # Truncate for context limits
---

Provide your analysis in a structured format."""
        
        response = await self._generate(prompt, system_prompt)
        
        return {
            "summary": response,
            "analyzed_at": datetime.utcnow().isoformat(),
            "provider": self.provider,
            "document_type": document_type
        }
    
    async def generate_case_recommendations(
        self, 
        case_description: str,
        document_summaries: list[str]
    ) -> Dict[str, Any]:
        """
        Generate recommendations for a case based on description and documents.
        
        Args:
            case_description: User's description of their land dispute
            document_summaries: List of AI-generated document summaries
            
        Returns:
            Dict containing recommendations and next steps
        """
        system_prompt = """You are a legal advisor AI assistant for land disputes in India.
Provide helpful, actionable recommendations based on the case details.
Always recommend consulting with a qualified legal professional for specific advice.
Be empathetic to the user's situation while remaining factual."""
        
        docs_text = "\n\n".join(document_summaries) if document_summaries else "No documents provided yet."
        
        prompt = f"""Based on the following case details, provide recommendations:

Case Description:
{case_description}

Document Analysis:
{docs_text}

Please provide:
1. Initial assessment of the case
2. Recommended immediate actions
3. Documents that should be obtained
4. Potential legal options to explore
5. Estimated timeline considerations
6. Important warnings or considerations

Format your response clearly with numbered sections."""
        
        response = await self._generate(prompt, system_prompt)
        
        return {
            "recommendations": response,
            "generated_at": datetime.utcnow().isoformat(),
            "provider": self.provider
        }
    
    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract named entities from document text.
        
        Identifies people, places, dates, measurements relevant to land disputes.
        
        FUTURE: Use dedicated NER models for better accuracy
        """
        system_prompt = """You are an entity extraction system for legal documents.
Extract and categorize entities accurately. Only extract entities that are explicitly mentioned.
Return entities in a structured format."""
        
        prompt = f"""Extract the following entities from this legal document text:

1. PERSONS: Names of individuals mentioned
2. ORGANIZATIONS: Companies, government bodies, courts
3. LOCATIONS: Places, addresses, localities
4. DATES: All dates mentioned
5. LAND_DETAILS: Survey numbers, plot numbers, area measurements
6. MONETARY: Any monetary amounts mentioned
7. LEGAL_REFS: Case numbers, act references, section numbers

Text:
---
{text[:3000]}
---

Format as:
PERSONS: [list]
ORGANIZATIONS: [list]
LOCATIONS: [list]
DATES: [list]
LAND_DETAILS: [list]
MONETARY: [list]
LEGAL_REFS: [list]"""
        
        response = await self._generate(prompt, system_prompt)
        
        # Parse response into structured format
        # FUTURE: Use structured output format (JSON mode) for reliable parsing
        return {
            "raw_extraction": response,
            "extracted_at": datetime.utcnow().isoformat(),
            "provider": self.provider
        }
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
_analyzer: Optional[DocumentAnalyzer] = None


def get_document_analyzer() -> DocumentAnalyzer:
    """
    Get or create the document analyzer instance.
    
    PRODUCTION: Consider dependency injection with FastAPI's Depends()
    for better testability.
    """
    global _analyzer
    if _analyzer is None:
        _analyzer = DocumentAnalyzer()
    return _analyzer


# =============================================================================
# USAGE EXAMPLE
# =============================================================================
#
# from app.agents.document_analyzer import get_document_analyzer
# 
# async def process_document(text: str):
#     analyzer = get_document_analyzer()
#     summary = await analyzer.summarize_document(text, "land deed")
#     return summary
#
# =============================================================================
