"""
Module defining the canonical Evidence model schema.

Standardizes the structure of the evidence metadata produced by specialist agents
(e.g., Provider Agent, Policy Agent, Pattern Agent) during claim analysis.
"""

from datetime import datetime, UTC
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.enums import AgentName, Severity


class Evidence(BaseModel):
    """
    Unified flat representation of any structured verification or validation outcome evidence.
    """
    evidence_id: str = Field(description="Unique tracking identifier for this specific verification piece.")
    mission_id: str = Field(description="Alphanumeric identifier matching the target adjudication mission.")
    agent: AgentName = Field(description="The specialist AI Agent that analyzed the data.")
    source: str = Field(description="The source or channel from which evidence was pulled (e.g., 'mcp', 'rule_engine').")
    title: str = Field(description="Short, human-readable visual summary of the finding.")
    description: str = Field(description="Verbose explanation details or reasoning of the verification check.")
    confidence: int = Field(ge=0, le=100, description="Accuracy or validation certainty percentage (0-100).")
    severity: Severity = Field(description="Log and alert coloring severity mapping.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="UTC timestamp when evidence was created.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom unstructured dictionary containing raw endpoint parameters.")
