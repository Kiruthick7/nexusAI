"""
Module declaring domain models representing final adjudication decisions.
"""

from pydantic import BaseModel, Field


class Decision(BaseModel):
    """
    Domain representation of an expense claim adjudication outcome.
    """
    status: str = Field(..., description="Final status decision (e.g., APPROVED, REJECTED, ESCALATED).")
    subtext: str = Field(..., description="Subtext reason details (e.g., 'DUPLICATE', 'MANUAL REVIEW REQUIRED').")
    duration_seconds: float = Field(..., description="Total time taken to complete orchestration.")
    agents_count: int = Field(..., description="Number of agents invoked during active run.")
    audit_trail_count: int = Field(..., description="Number of logging checkpoints registered in run.")
