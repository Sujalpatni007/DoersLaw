"""
DOER Platform - Voice-to-Text Processing

Handles audio file transcription for voice-based dispute filing.
Uses OpenAI Whisper API with caching for cost optimization.

SUPPORTED FORMATS:
- WAV, MP3, M4A, WEBM, OGG

PRODUCTION UPGRADES:
- Implement audio file caching by hash
- Add support for long audio via chunking
- Use cheaper local Whisper model for standard cases
- Add noise reduction preprocessing
"""

import os
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path


# Audio configuration
SUPPORTED_AUDIO_FORMATS = {
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
}

MAX_AUDIO_SIZE_MB = 25  # OpenAI Whisper limit


class VoiceProcessor:
    """
    Voice-to-text processor using OpenAI Whisper API.
    
    Includes caching to minimize API costs.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the voice processor.
        
        Args:
            api_key: OpenAI API key. Uses env var if not provided.
            cache_dir: Directory for caching transcriptions.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.cache_dir = Path(cache_dir or self._default_cache_dir())
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._client = None
    
    def _default_cache_dir(self) -> str:
        """Get default cache directory."""
        return str(Path(__file__).parent.parent.parent / "data" / "audio_cache")
    
    def _get_client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "OpenAI API key required. Set OPENAI_API_KEY environment variable."
                )
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. Run: pip install openai"
                )
        return self._client
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate file hash for caching."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _get_cache_path(self, file_hash: str) -> Path:
        """Get cache file path for given hash."""
        return self.cache_dir / f"{file_hash}.txt"
    
    def _check_cache(self, file_hash: str) -> Optional[str]:
        """Check if transcription is cached."""
        cache_path = self._get_cache_path(file_hash)
        if cache_path.exists():
            return cache_path.read_text(encoding='utf-8')
        return None
    
    def _save_cache(self, file_hash: str, transcription: str) -> None:
        """Save transcription to cache."""
        cache_path = self._get_cache_path(file_hash)
        cache_path.write_text(transcription, encoding='utf-8')
    
    def validate_audio_file(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        """
        Validate audio file before processing.
        
        Args:
            file_path: Path to audio file
            mime_type: MIME type of file
            
        Returns:
            Dict with validation result
        """
        errors = []
        
        # Check file exists
        if not os.path.exists(file_path):
            errors.append("File not found")
            return {"valid": False, "errors": errors}
        
        # Check format
        if mime_type not in SUPPORTED_AUDIO_FORMATS:
            errors.append(f"Unsupported format: {mime_type}")
        
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > MAX_AUDIO_SIZE_MB:
            errors.append(f"File too large: {file_size_mb:.2f}MB (max: {MAX_AUDIO_SIZE_MB}MB)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "file_size_mb": file_size_mb
        }
    
    async def transcribe(
        self,
        file_path: str,
        language: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.
        
        Args:
            file_path: Path to audio file
            language: Optional language hint (e.g., 'hi', 'en')
            use_cache: Whether to use cached results
            
        Returns:
            Dict with transcription result
        """
        # Check cache first
        if use_cache:
            file_hash = self._get_file_hash(file_path)
            cached = self._check_cache(file_hash)
            if cached:
                return {
                    "text": cached,
                    "cached": True,
                    "language": language,
                    "file_path": file_path
                }
        else:
            file_hash = None
        
        try:
            client = self._get_client()
            
            with open(file_path, 'rb') as audio_file:
                # Prepare transcription parameters
                params = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "text"
                }
                
                if language:
                    params["language"] = language
                
                # Call Whisper API
                transcription = client.audio.transcriptions.create(**params)
            
            result_text = transcription if isinstance(transcription, str) else transcription.text
            
            # Cache the result
            if use_cache and file_hash:
                self._save_cache(file_hash, result_text)
            
            return {
                "text": result_text,
                "cached": False,
                "language": language,
                "file_path": file_path
            }
            
        except Exception as e:
            return {
                "text": None,
                "error": str(e),
                "cached": False,
                "file_path": file_path
            }
    
    def transcribe_sync(
        self,
        file_path: str,
        language: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Synchronous version of transcribe for non-async contexts.
        """
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self.transcribe(file_path, language, use_cache)
            )
        finally:
            loop.close()


# Singleton instance
_processor: Optional[VoiceProcessor] = None


def get_voice_processor() -> VoiceProcessor:
    """Get or create the voice processor instance."""
    global _processor
    if _processor is None:
        _processor = VoiceProcessor()
    return _processor


def transcribe_audio(file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to transcribe audio.
    
    Args:
        file_path: Path to audio file
        language: Optional language hint
        
    Returns:
        Transcription result
    """
    processor = get_voice_processor()
    return processor.transcribe_sync(file_path, language)
