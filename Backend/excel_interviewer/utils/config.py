"""
Configuration management for Excel Mock Interviewer
"""
from pydantic import BaseSettings, Field, validator
from typing import Optional, List, Dict, Any

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = Field(default="Excel Mock Interviewer")
    version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    environment: str = Field(default="development")
    
    # Server settings
    host: str = Field(default="localhost")
    port: int = Field(default=8000)
    
    # Database settings
    database_url: str = Field(default="postgresql://user:password@localhost:5432/excel_interviewer")
    database_echo: bool = Field(default=False)
    
    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_password: Optional[str] = Field(default=None)
    redis_db: int = Field(default=0)
    redis_timeout: int = Field(default=5)
    
    # AI/LLM settings
    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)
    default_model: str = Field(default="gpt-4")
    max_tokens: int = Field(default=1000)
    temperature: float = Field(default=0.7)
    
    # Interview settings
    max_questions_per_interview: int = Field(default=15)
    default_time_limit_minutes: int = Field(default=45)
    passing_score_threshold: float = Field(default=60.0)
    
    # API settings
    api_prefix: str = Field(default="/api/v1")
    cors_origins: List[str] = Field(default=["http://localhost:8501", "http://127.0.0.1:8501"])
    rate_limit_requests_per_minute: int = Field(default=100)
    
    # Logging settings
    log_level: str = Field(default="INFO")
    log_file: Optional[str] = Field(default="excel_interviewer.log")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()
