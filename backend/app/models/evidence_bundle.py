"""
Module declaring the structured EvidenceBundle contract.
Collects and groups evidence from all participating specialist agents.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.evidence import Evidence


class EvidenceBundle(BaseModel):
    """
    Unified group of all evidence findings compiled from the specialist agents
    prior to submitting to the Arbiter decision engine.
    """
    mission_id: str = Field(description="Alphanumeric tracking identifier of the active adjudication run.")
    provider_findings: Optional[Evidence] = Field(default=None, description="Compiled evidence from the Provider verification agent.")
    policy_findings: Optional[Evidence] = Field(default=None, description="Compiled evidence from the Policy auditing agent.")
    pattern_findings: Optional[Evidence] = Field(default=None, description="Compiled evidence from the Pattern fraud and behavioral analytics agent.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Raw dictionary containing workflow and planner execution parameters.")
