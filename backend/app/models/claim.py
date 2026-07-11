"""
Module declaring domain models representing expense and validation claims.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Claim(BaseModel):
    """
    Domain representation of an expense claim submitted for AI adjudication.
    """
    id: str = Field(..., description="Unique alphanumeric tracking ID (e.g. NEX-4012).")
    invoice_name: str = Field(..., description="Original PDF file name or source label.")
    invoice_size: str = Field(..., description="Human-readable file size metrics (e.g. '1.4 MB').")
    vendor_name: str = Field(..., description="Name of the invoice merchant or medical provider.")
    category: str = Field(..., description="Broad category of expense (e.g., Medical Equipment, Travel).")
    gstin: Optional[str] = Field(None, description="Goods and Services Tax Identification Number (if applicable).")
    member_id: Optional[str] = Field(None, description="Insurance policy or company member membership ID.")
    extracted_confidence: int = Field(default=95, ge=0, le=100, description="Confidence percentage during scanning.")
