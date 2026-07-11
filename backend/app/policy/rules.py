"""
Module defining Pydantic model schemas for corporate policy controls and rule findings.
"""

from datetime import datetime, UTC
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.enums import Severity


class PolicyRuleConfig(BaseModel):
    """
    Validation configurations loaded for a single corporate category.
    """
    max_amount: float = Field(..., description="Absolute maximum allowable claim threshold.")
    receipt_required: bool = Field(True, description="Whether receipt/invoice documentation is required.")
    allowed_currencies: List[str] = Field(default_factory=lambda: ["INR", "USD"], description="List of authorized ISO codes.")
    required_fields: List[str] = Field(default_factory=lambda: ["vendor_name", "date", "amount"], description="Mandatory fields.")
    approval_threshold: float = Field(..., description="Threshold above which claims get flagged for human gates.")


class PolicyFinding(BaseModel):
    """
    Structured outcome representing the evaluation of a single policy control.
    """
    rule: str = Field(..., description="Name of the corporate policy check.")
    result: str = Field(..., description="Result value: PASS | FLAG | HARD_FAIL")
    details: str = Field(..., description="Details and context regarding compliance or violation findings.")
    confidence: int = Field(default=100, ge=0, le=100, description="Verification certainty.")
    severity: Severity = Field(..., description="Visual severity color indicator.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="ISO datetime of the check run.")
