"""
Module defining the canonical Shared Mission Context for downstream agent evaluations.

Future agents should exclusively consume this unified state model rather than
re-analyzing raw uploaded documents or images.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SharedMissionContext(BaseModel):
    """
    State representation containing extracted data, confidence metrics, and raw metadata
    emitted by the Intake Agent and shared with other downstream agent nodes.
    """
    mission_id: str = Field(..., description="Unique alphanumeric tracking run ID.")
    claim_id: str = Field(..., description="Unique alphanumeric tracking claim ID.")
    
    # Normalized extracted fields
    vendor_name: Optional[str] = Field(None, description="Normalized name of the vendor.")
    gstin: Optional[str] = Field(None, description="Normalized Goods and Services Tax Identification Number.")
    invoice_number: Optional[str] = Field(None, description="Normalized tracking invoice reference string.")
    amount: Optional[float] = Field(None, description="Normalized final monetary total.")
    currency: Optional[str] = Field(None, description="ISO-3 letter currency code representation (e.g., INR).")
    date: Optional[str] = Field(None, description="ISO-8601 formatted date (YYYY-MM-DD).")
    category: Optional[str] = Field(None, description="Inferred corporate categorization code.")
    employee_id: Optional[str] = Field(None, description="Normalized tracking employee code.")
    
    # Confidence metrics
    confidence: Dict[str, float] = Field(
        default_factory=dict,
        description="Fractions from 0.00 to 1.00 mapping extraction certainty for each field."
    )
    
    # Raw references
    raw_ocr_text: Optional[str] = Field(None, description="Full OCR raw dump text parsed from invoice.")
    
    # Extensible metadata dictionary
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom context parameters passed between agents."
    )
