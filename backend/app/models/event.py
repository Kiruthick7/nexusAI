"""
Module declaring domain models representing platform system events.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class Event(BaseModel):
    """
    Domain representation of a real-time event dispatched over Server-Sent Events (SSE).
    """
    event_id: str = Field(..., description="Unique UUID or sequential identifier tracking this transaction.")
    event_type: str = Field(..., description="Canonical event name (e.g. 'workflow_started', 'conflict_detected').")
    timestamp: str = Field(..., description="ISO 8601 formatted datetime string of the event instance.")
    mission_id: str = Field(..., description="The parent workflow tracking session ID.")
    step: str = Field(..., description="Current state-machine workflow step (e.g. INGESTING, PLANNING).")
    severity: str = Field(default="INFO", description="Visual indicator status (e.g. INFO, WARN, ERROR, SUCCESS).")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Custom dictionary holding structured values.")
