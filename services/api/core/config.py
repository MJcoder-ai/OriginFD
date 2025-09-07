"""
Core configuration settings for OriginFD API.
"""
from functools import lru_cache
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Application
    PROJECT_NAME: str = "OriginFD"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Security
    SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = Field(env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    REDIS_EXPIRE_TIME: int = Field(default=3600, env="REDIS_EXPIRE_TIME")
    
    # CORS
    ALLOWED_HOSTS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="ALLOWED_HOSTS"
    )
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Google Cloud
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(default=None, env="GOOGLE_CLOUD_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(
        default=None, env="GOOGLE_APPLICATION_CREDENTIALS"
    )
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_PERIOD: int = Field(default=60, env="RATE_LIMIT_PERIOD")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse ALLOWED_HOSTS from string if needed."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment values."""
        allowed = ["development", "testing", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8", 
        "case_sensitive": True,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()