"""
Module defining the centralized configuration settings for the Nexus AI Operations Platform.

Loads and validates environment variables dynamically using Pydantic Settings v2.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration schema.
    
    Reads values from environment variables or a local .env file.
    """
    # FastAPI Application Config
    PORT: int = 8000
    DEBUG: bool = True
    
    # AI/ML Provider configs
    GEMINI_API_KEY: Optional[str] = None
    MODEL_NAME: Optional[str] = None
    MODEL_NAME_TTS: Optional[str] = None
    
    # Google Cloud Platform (GCP) configurations
    GCP_PROJECT_ID: Optional[str] = None
    BQ_DATASET: Optional[str] = None
    GCS_BUCKET: Optional[str] = None
    
    # Neon Serverless PostgreSQL url
    NEON_DATABASE_URL: Optional[str] = None

    # Load from system environment and optional .env files
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate a singleton configuration instance
settings = Settings()
