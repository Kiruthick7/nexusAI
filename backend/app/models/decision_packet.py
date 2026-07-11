"""
Module declaring the single unified DecisionPacket contract for frontend consumption.
Integrates all specialist evidence, conflicts, resolution rounds, human questions, and audit metrics.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.models.evidence import Evidence


class DecisionPacket(BaseModel):
    """
    The ultimate self-documenting payload returned from the Arbiter Decision Engine.
    Exposes unified operational state for frontend presentation and real-time SSE streaming.
    """
    mission: str = Field(description="Alphanumeric tracking identifier of the adjudication mission.")
    recommendation: str = Field(description="Deterministic decision outcome recommendation (APPROVE, REJECT, ESCALATE).")
    reason: str = Field(description="Clear, explainable rationale summarizing why this decision recommendation was reached.")
    confidence: int = Field(ge=0, le=100, description="Recalculated weighted aggregate confidence metric (0-100).")
    provider_evidence: Optional[Evidence] = Field(default=None, description="The complete Provider Specialist evidence if triggered.")
    policy_evidence: Optional[Evidence] = Field(default=None, description="The complete Policy Specialist evidence if triggered.")
    pattern_evidence: Optional[Evidence] = Field(default=None, description="The complete Pattern Specialist evidence if triggered.")
    conflicts: List[Dict[str, Any]] = Field(default_factory=list, description="List of any transactional or evidence conflicts identified.")
    human_question: Optional[str] = Field(default=None, description="Human-in-the-loop validation question required for ESCALATE cases.")
    timeline: List[Dict[str, Any]] = Field(default_factory=list, description="Sequential log stream or checklist transition timeline.")
    audit_summary: Dict[str, Any] = Field(default_factory=dict, description="Metadata audit metrics explaining timestamp, latency, and rule conditions.")
