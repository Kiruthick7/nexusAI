"""
Module defining the Pydantic schemas for the Pattern Agent.
"""

from datetime import datetime, UTC
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.models.enums import Severity


class PatternFinding(BaseModel):
    """
    Structured outcome representing the evaluation of a single behavioral or anomaly check.
    """
    pattern_type: str = Field(..., description="The behavioral pattern check type (e.g. duplicate_invoice, repeated_vendor).")
    severity: Severity = Field(..., description="Visual severity color indicator (PASS -> SUCCESS, FLAG -> WARN, HARD_FAIL -> ERROR).")
    result: str = Field(..., description="Result value: PASS | FLAG | HARD_FAIL")
    evidence: str = Field(..., description="A clear, human-readable summary of the evidence found.")
    confidence: int = Field(default=100, ge=0, le=100, description="Confidence score in the check.")
    supporting_claims: List[Dict[str, Any]] = Field(default_factory=list, description="Historical claims that support or trigger this finding.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
