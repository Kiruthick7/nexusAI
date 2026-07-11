"""
Module defining domain Pydantic models for the Gemma Intelligence Layer.
Holds validation schemas for client payloads, API endpoints, and structured LLM outputs.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class GemmaExplanationPacket(BaseModel):
    """
    Canonical API response schema containing independent, human-readable explanations,
    persona-targeted summaries, and logical auditing reviews produced by Gemma.
    """
    mission_id: str = Field(description="Unique alphanumeric tracking ID of the adjudication run.")
    behavior_summary: Optional[str] = Field(None, description="Explanation describing unusual claim behavior (Max 80 words).")
    decision_explanation: Optional[str] = Field(None, description="Detailed human-readable explanation justifying approved, rejected, or escalated outcome.")
    executive_summary: Optional[str] = Field(None, description="General executive summary (Max 60 words).")
    finance_summary: Optional[str] = Field(None, description="Finance-focused executive summary (Max 60 words).")
    employee_summary: Optional[str] = Field(None, description="Employee-oriented summary explaining the outcome (Max 60 words).")
    decision_review: Optional[str] = Field(None, description="Determined status (MATCH or REVIEW) and supporting audit explanation.")
    generated_at: str = Field(description="ISO 8601 UTC timestamp capturing compilation time.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata parameters capturing executing model name and diagnostic latency.")


class GemmaGenerationTarget(BaseModel):
    """
    Structured generation target schema mapping Gemma's complete analysis tasks.
    Aggregating fields into a single model minimizes API call latency and token cost.
    """
    behavior_summary: str = Field(
        description="Concise description of any unusual claim behaviors, duplicates, or anomalies detected. Max 80 words."
    )
    decision_explanation: str = Field(
        description="Human-readable justification detailing why the claim was APPROVED, REJECTED, or ESCALATED. Reference specialist evidence. Max 120 words. Do not invent facts."
    )
    executive_summary: str = Field(
        description="High-level corporate brief of the claim context. Max 60 words."
    )
    finance_summary: str = Field(
        description="Finance-focused executive brief emphasizing budgets, rules, and costs. Max 60 words."
    )
    employee_summary: str = Field(
        description="Friendly, employee-oriented summary explaining the adjudication outcome. Max 60 words."
    )
    review_status: str = Field(
        description="MATCH or REVIEW. MATCH if the Arbiter's recommendation aligns logically with specialist findings, REVIEW if potential conflict or logical gap exists."
    )
    review_explanation: str = Field(
        description="Short explanation justifying the MATCH or REVIEW audit selection. Max 50 words."
    )
