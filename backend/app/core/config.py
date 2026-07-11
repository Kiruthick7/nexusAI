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
    GOOGLE_API_KEY: Optional[str] = None
    MODEL_NAME: Optional[str] = None
    MODEL_NAME_TTS: Optional[str] = None
    MODEL_NAME_LIVE: Optional[str] = None
    MODEL_NAME_TRANSLATE: Optional[str] = None
    MODEL_NAME_IMAGE: Optional[str] = None
    MODEL_NAME_OMNI: Optional[str] = None
    INTERACTIONS_MODEL: Optional[str] = None
    GEMMA_MODEL: Optional[str] = "gemma2-27b-it"
    
    # Google Cloud Platform (GCP) configurations
    GCP_PROJECT_ID: Optional[str] = None
    BQ_DATASET: Optional[str] = None
    GCS_BUCKET: Optional[str] = None
    CLOUD_SQL_CONNECTION_NAME: Optional[str] = None
    CLOUD_SQL_DATABASE: Optional[str] = None
    CLOUD_SQL_USER: Optional[str] = None
    CLOUD_SQL_PASSWORD: Optional[str] = None
    
    # Hugging Face endpoint / local model override
    HF_API_KEY: Optional[str] = None
    HF_ENDPOINT: Optional[str] = None
    LOCAL_MODEL: Optional[str] = "gemma-4-e4b"

    # Demo Mode
    DEMO_MODE: bool = False

    # Load from system environment and optional .env files
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate a singleton configuration instance
settings = Settings()


def validate_startup_config() -> None:
    """
    Validates that all required operational parameters are populated.
    If incomplete, fails fast unless DEMO_MODE is active.
    """
    import sys
    required_keys = [
        "GOOGLE_API_KEY",
        "MODEL_NAME",
        "MODEL_NAME_TTS",
        "MODEL_NAME_LIVE",
        "MODEL_NAME_TRANSLATE",
        "MODEL_NAME_IMAGE",
        "MODEL_NAME_OMNI",
        "INTERACTIONS_MODEL",
        "GEMMA_MODEL",
        "GCP_PROJECT_ID",
        "BQ_DATASET",
        "GCS_BUCKET",
        "CLOUD_SQL_CONNECTION_NAME",
        "CLOUD_SQL_DATABASE",
        "CLOUD_SQL_USER",
        "CLOUD_SQL_PASSWORD"
    ]
    
    missing = []
    for key in required_keys:
        val = getattr(settings, key, None)
        if val is None or str(val).strip() == "":
            missing.append(key)
            
    if missing:
        if settings.DEMO_MODE:
            print("\n" + "=" * 80, file=sys.stderr)
            print("⚠️  [DEMO WARNING] Startup configuration is incomplete!", file=sys.stderr)
            print("Missing variables: " + ", ".join(missing), file=sys.stderr)
            print("Since DEMO_MODE=true, the platform will continue in offline mode.", file=sys.stderr)
            print("=" * 80 + "\n", file=sys.stderr)
        else:
            print("\n" + "!" * 80, file=sys.stderr)
            print("❌  [FATAL ERROR] Startup configuration is incomplete! App shutting down.", file=sys.stderr)
            print("Missing required variables: " + ", ".join(missing), file=sys.stderr)
            print("To bypass this during local testing/mock demo, set DEMO_MODE=true.", file=sys.stderr)
            print("!" * 80 + "\n", file=sys.stderr)
            sys.exit(1)


# Perform configuration verification upon bootstrapping
validate_startup_config()
