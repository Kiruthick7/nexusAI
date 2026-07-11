"""
Module declaring specific internal Pydantic models for the Arbiter Decision Engine.
Includes conflict matching schemas, resolution summaries, and recommendation contracts.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Conflict(BaseModel):
    """
    Represents a specific registered discrepancy or disagreement identified between specialist agent findings.
    """
    conflict_id: str = Field(description="Unique tracking ID for this specific conflict instance.")
    severity: str = Field(description="Conflict severity status color mapping (e.g. WARN, ERROR).")
    description: str = Field(description="Detailed narrative explaining the logical conflict matching criteria.")
    conflicting_agents: List[str] = Field(description="List of specialist agent names that returned opposing evidence.")


class ResolutionResult(BaseModel):
    """
    Represents the mathematical and narrative outcome of a single structured conflict resolution round.
    """
    resolved: bool = Field(default=True, description="Indicates if the resolution round was able to reach a logical consensus.")
    resolution_summary: str = Field(description="Explainable breakdown of the evidence weighting and balance checks.")
    remaining_disagreement: str = Field(description="Narrative detailing any unresolved boundary friction points.")
    recalculated_confidence: int = Field(ge=0, le=100, description="Confidence recalculated based on agent reliability weights.")
    recommended_action: str = Field(description="Deterministic directional outcome deduced from the resolution math.")
