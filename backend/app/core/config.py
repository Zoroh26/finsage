"""
Application Configuration
Centralized settings management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "FinSage"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str

    # MCP Server
    FI_MCP_BASE_URL: str = "http://localhost:8080"
    FI_MCP_STREAM_ENDPOINT: str = "/mcp/stream"  # Added from .env
    USE_SAMPLE_MCP_DATA: bool = False

    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
