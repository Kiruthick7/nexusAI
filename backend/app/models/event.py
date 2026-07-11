"""
Module declaring domain models representing platform system events.

Every published event matches this exact, unified flat schema of 13 fields.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.enums import EventType, AgentName, AgentStatus, Severity


class Event(BaseModel):
    """
    Domain representation of a real-time event dispatched over Server-Sent Events (SSE).
    """
    event_id: str = Field(..., description="Unique alphanumeric tracking or UUID code.")
    mission_id: str = Field(..., description="The parent workflow tracking session ID.")
    event_type: EventType = Field(..., description="Canonical event name checkpoint label.")
    agent: Optional[AgentName] = Field(default=None, description="The executing agent name.")
    status: Optional[AgentStatus] = Field(default=None, description="Active status of the executing agent.")
    title: str = Field(..., description="Short title text explaining checkpoint.")
    message: str = Field(..., description="Verbose description detail or log message.")
    severity: Severity = Field(..., description="Visual log status indicator (INFO, SUCCESS, WARN, ERROR).")
    confidence: Optional[int] = Field(default=None, ge=0, le=100, description="Confidence metrics.")
    latency_ms: Optional[int] = Field(default=None, ge=0, description="Latency measure in milliseconds.")
    tools_used: List[str] = Field(default_factory=list, description="Array of executed developer tools.")
    timestamp: datetime = Field(..., description="Datetime timestamp of event instantiation.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom dictionary holding structured payload values.")
