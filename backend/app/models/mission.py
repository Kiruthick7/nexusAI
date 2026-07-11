"""
Module declaring domain models representing active mission running states.
"""

from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel, Field
from app.models.enums import WorkflowStatus


class Mission(BaseModel):
    """
    Domain representation of an active AI expense adjudication run session (Mission).
    """
    mission_id: str = Field(..., description="Unique alphanumeric session ID (e.g. RUN-9081).")
    claim_id: str = Field(..., description="Associated domain Claim payload ID under evaluation.")
    workflow_status: WorkflowStatus = Field(default=WorkflowStatus.IDLE, description="High-level processing stage status of mission.")
    current_stage: str = Field(default="IDLE", description="Short tag representing active lifecycle progress.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last updated timestamp.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom dictionary holding structured running states.")


class AgentState(BaseModel):
    """
    Domain representation of a parallel agent evaluation status track.
    """
    agent_name: str = Field(..., description="The key of the tracking agent.")
    status: str = Field(..., description="Current status string.")
    message: str = Field(..., description="Latest checkpoint notification.")
    updated_at: datetime = Field(..., description="Last updated timestamp.")
