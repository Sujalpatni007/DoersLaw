"""
DOER Platform - Configuration Settings

This module contains all application settings using Pydantic Settings.
Settings can be overridden via environment variables or a .env file.

PRODUCTION UPGRADES:
- DATABASE_URL: Change from sqlite to postgresql://user:pass@host:5432/doer_db
- AWS_* settings: Uncomment and configure for S3 file storage
- REDIS_URL: Uncomment for caching and session management
- AI_PROVIDER: Switch from 'ollama' to 'openai' for cloud AI
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "DOER Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Database
    # PRODUCTION: Change to "postgresql+asyncpg://user:password@localhost:5432/doer_db"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/doer.db"
    
    # JWT Authentication
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # File Storage
    # PRODUCTION: Set to "s3" and configure AWS settings below
    STORAGE_PROVIDER: str = "local"
    UPLOAD_DIR: str = "./data/uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: str = "pdf,jpg,jpeg,png,doc,docx"
    
    # AWS S3 Settings (PRODUCTION)
    # Uncomment these for production S3 usage:
    # AWS_ACCESS_KEY_ID: Optional[str] = None
    # AWS_SECRET_ACCESS_KEY: Optional[str] = None
    # AWS_REGION: str = "ap-south-1"
    # S3_BUCKET_NAME: str = "doer-documents"
    
    # Redis Cache (PRODUCTION)
    # Uncomment for production caching:
    # REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI Configuration
    # Set to "openai" for cloud AI, "ollama" for local
    AI_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    
    # OpenAI Settings (PRODUCTION)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_RATE_LIMIT_RPM: int = 20  # Requests per minute
    
    # SMS/WhatsApp (Twilio)
    # PRODUCTION: Set actual Twilio credentials
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    SMS_SIMULATION_MODE: bool = True  # Set to False in production
    
    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3050,http://localhost:4000,http://localhost:5173"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures settings are only loaded once.
    PRODUCTION: Consider using a proper secrets manager like AWS Secrets Manager.
    """
    return Settings()
