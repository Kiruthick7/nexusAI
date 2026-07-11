"""
Module defining the canonical EscalationPacket model for the Nexus AI Operations Platform.

Holds synthesized findings, decision rationale, specific human audit questions,
and Text-to-Speech audio details to support manual claim verification workflows.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class EscalationPacket(BaseModel):
    """
    Structured escalation review package containing all necessary context for a human auditor.
    Included inside REST responses and stored permanently in mission records.
    """
    mission_id: str = Field(description="Unique alphanumeric tracking ID of the active adjudication run.")
    claim_id: str = Field(description="Unique alphanumeric tracking ID of the expense claim.")
    summary: str = Field(description="Concise finance-oriented executive summary (< 120 words).")
    recommendation: str = Field(description="Deterministic Arbiter recommendation (typically ESCALATE).")
    human_question: str = Field(description="Exactly ONE clear, actionable review question for the manual auditor.")
    confidence: int = Field(ge=0, le=100, description="Adjudication weighted aggregate confidence score.")
    decision_reason: str = Field(description="High-level reasoning rationale explaining why escalation was triggered.")
    provider_summary: Optional[str] = Field(default=None, description="Concise summary of Provider Verification Specialist findings.")
    policy_summary: Optional[str] = Field(default=None, description="Concise summary of Policy Specialist guidelines evaluation.")
    pattern_summary: Optional[str] = Field(default=None, description="Concise summary of Pattern Specialist behavioral anomaly logs.")
    gemma_summary: Optional[str] = Field(default=None, description="Synthetic pattern summary or secondary behavioral details.")
    audio_url: Optional[str] = Field(default=None, description="Google Cloud Storage signed URL or local fallback to play the spoken voice brief.")
    audio_duration: float = Field(default=0.0, description="Duration of the synthesized briefing audio in seconds.")
    generated_at: str = Field(description="ISO 8601 UTC timestamp capturing compilation time.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom dictionary holding extensible contextual execution metadata.")
