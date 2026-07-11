"""
Module declaring domain models representing platform health check status states.
"""

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """
    Domain representation of service health diagnostics.
    """
    status: str = Field(default="healthy", description="Status code indicating server wellness.")
    version: str = Field(default="1.0.0", description="Backend semantic project version.")
    uptime_seconds: float = Field(default=0.0, description="Uptime duration of current active process.")
