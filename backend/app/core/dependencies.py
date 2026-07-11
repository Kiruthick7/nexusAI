"""
Module declaring dependency injection parameters for use with Depends in FastAPI router paths.

De-couples framework routing from database clients, GCP connection handlers,
and underlying core services.
"""

from typing import Generator, AsyncGenerator
import httpx
from app.core.config import settings, Settings
from app.core.logger import logger


def get_settings() -> Settings:
    """
    Returns the centralized application Settings singleton configuration.
    """
    return settings


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    FastAPI dependency yielding a reusable async HTTP client.
    
    Guarantees proper closing of socket connections upon route teardown.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        yield client


def get_db_session() -> Generator[None, None, None]:
    """
    FastAPI dependency yielding database connection sessions.
    
    [PLACEHOLDER] To be fully implemented once database adapters (e.g. SQLModel/SQLAlchemy)
    are integrated.
    """
    logger.debug("Database dependency session requested (not implemented).")
    try:
        yield None
    finally:
        pass
