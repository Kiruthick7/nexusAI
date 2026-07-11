"""
Module declaring domain models representing active mission running states.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.claim import Claim
from app.models.decision import Decision


class Mission(BaseModel):
    """
    Domain representation of a complete AI expense adjudication run session (Mission).
    """
    id: str = Field(..., description="Unique alphanumeric session ID (e.g. RUN-9081).")
    claim: Claim = Field(..., description="Associated domain Claim payload under evaluation.")
    status: str = Field(default="IDLE", description="Active process phase status of mission (e.g. INGESTING, COMPLETED).")
    decision: Optional[Decision] = Field(None, description="The resolved outcome data of active run (if completed).")
    warnings: List[str] = Field(default_factory=list, description="Array of audit or conflict warning flags detected.")
