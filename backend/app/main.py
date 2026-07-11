"""
Main bootstrap module instantiating the minimal FastAPI application.

Exposes fundamental health checks and running verification endpoints. Does not contain
database adapters, LLM models, or business logic workflows at this stage.
"""

from fastapi import FastAPI
from app.core.config import settings
from app.core.logger import logger

# Initialize the central FastAPI application
app = FastAPI(
    title="Nexus AI Operations Platform",
    description="Event-Driven multi-agent enterprise expense adjudication backend API.",
    version="1.0.0",
    debug=settings.DEBUG,
)


@app.get("/")
def read_root() -> dict[str, str]:
    """
    Root endpoint verifying server active session states.
    
    Returns:
        JSON dictionary indicating service name and active status.
    """
    logger.debug("Root path GET '/' requested.")
    return {
        "service": "Nexus AI Operations Platform",
        "status": "running"
    }


@app.get("/health")
def read_health() -> dict[str, str]:
    """
    Health diagnostic endpoint for service orchestrations and container probes.
    
    Returns:
        JSON dictionary mapping status.
    """
    logger.info("Health diagnostics GET '/health' requested.")
    return {
        "status": "healthy"
    }
