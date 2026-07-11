"""
Module implementing the priority-based Provider Lookup registry.

Resolves provider credentials and MCP endpoint details using facts from the
SharedMissionContext. Priority levels are:
1. Exact GSTIN registration match.
2. Phone number match.
3. Vendor name case-insensitive substring comparison.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.mission_context import SharedMissionContext
from app.core.logger import logger


class ProviderLookupResult(BaseModel):
    """
    Structured registry response for resolved providers.
    """
    provider_name: str = Field(description="Normalized name of the registered provider.")
    gstin: str = Field(description="Active tax identifier or GSTIN registration.")
    provider_id: str = Field(description="Unique internal provider catalog identifier.")
    mcp_endpoint: str = Field(description="Target MCP server endpoint for real-time validation.")
    confidence: int = Field(ge=0, le=100, description="Lookup resolution confidence.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary provider details.")


# Mock provider registry database representing compliant medical, hospital, and technology providers
MOCK_PROVIDER_REGISTRY = [
    {
        "provider_name": "Apollo Hospitals",
        "gstin": "GSTIN-987654321",
        "phone": "9876543210",
        "provider_id": "PROV-APOLLO",
        "mcp_endpoint": "http://localhost:8081/mcp",
        "metadata": {"specialty": "Healthcare", "tier": "Enterprise"}
    },
    {
        "provider_name": "Apollo Clinics",
        "gstin": "GSTIN-APOLLO-CLINIC",
        "phone": "2125550198",
        "provider_id": "PROV-APOLLO-CLINIC",
        "mcp_endpoint": "http://localhost:8081/mcp",
        "metadata": {"specialty": "Healthcare", "tier": "Enterprise"}
    },
    {
        "provider_name": "DeepMind Corp",
        "gstin": "GST-123456",
        "phone": "1234567890",
        "provider_id": "PROV-DEEPMIND",
        "mcp_endpoint": "http://localhost:8082/mcp",
        "metadata": {"specialty": "Technology", "tier": "Enterprise"}
    },
    {
        "provider_name": "Max Healthcare",
        "gstin": "GSTIN-111222333",
        "phone": "1112223330",
        "provider_id": "PROV-MAX",
        "mcp_endpoint": "http://localhost:8083/mcp",
        "metadata": {"specialty": "Healthcare", "tier": "Premium"}
    },
    {
        "provider_name": "Offline Pharmacy",
        "gstin": "GST-OFFLINE",
        "phone": "9999999999",
        "provider_id": "PROV-OFFLINE",
        "mcp_endpoint": "http://localhost:8084/mcp-offline",
        "metadata": {"specialty": "Pharmacy", "tier": "Local"}
    },
    {
        "provider_name": "Slow Laboratory",
        "gstin": "GST-SLOW",
        "phone": "8888888888",
        "provider_id": "PROV-SLOW",
        "mcp_endpoint": "http://localhost:8085/mcp-slow",
        "metadata": {"specialty": "Laboratory", "tier": "Local"}
    },
    {
        "provider_name": "Mismatched Clinic",
        "gstin": "GST-MISMATCH",
        "phone": "7777777777",
        "provider_id": "PROV-MISMATCH",
        "mcp_endpoint": "http://localhost:8086/mcp-mismatch",
        "metadata": {"specialty": "General Medicine", "tier": "Standard"}
    }
]


def resolve_provider(context: SharedMissionContext) -> Optional[ProviderLookupResult]:
    """
    Performs cascading lookup to resolve target provider and its MCP endpoint.
    
    Resolution Priority:
    1. Exact GSTIN match (Priority 1)
    2. Phone number match (Priority 2)
    3. Vendor name case-insensitive comparison (Priority 3)
    
    Returns:
        ProviderLookupResult if a match with high confidence is identified, otherwise None.
    """
    logger.debug(f"[PROVIDER LOOKUP] Initiating cascading lookup for vendor={context.vendor_name}, gstin={context.gstin}")
    
    # 1. Exact GSTIN matching (Priority 1)
    if context.gstin:
        gstin_clean = context.gstin.strip().upper()
        for prov in MOCK_PROVIDER_REGISTRY:
            if prov["gstin"].strip().upper() == gstin_clean:
                logger.info(f"[PROVIDER LOOKUP] Match found via GSTIN (Priority 1): {prov['provider_name']}")
                return ProviderLookupResult(
                    provider_name=prov["provider_name"],
                    gstin=prov["gstin"],
                    provider_id=prov["provider_id"],
                    mcp_endpoint=prov["mcp_endpoint"],
                    confidence=100,
                    metadata=prov["metadata"]
                )

    # 2. Phone number matching (Priority 2)
    # Extracted phone is optional. Let's check metadata or context dictionary if exists,
    # or look up custom keys. Since SharedMissionContext has raw_ocr_text and confidence dicts,
    # let's look inside metadata if phone number was registered.
    # In case there's no direct phone attribute on context, we check if it is passed in the context metadata.
    context_phone = context.metadata.get("phone") if context.metadata else None
    if context_phone:
        phone_clean = "".join(filter(str.isdigit, str(context_phone)))
        for prov in MOCK_PROVIDER_REGISTRY:
            prov_phone = "".join(filter(str.isdigit, prov["phone"]))
            if prov_phone == phone_clean:
                logger.info(f"[PROVIDER LOOKUP] Match found via Phone (Priority 2): {prov['provider_name']}")
                return ProviderLookupResult(
                    provider_name=prov["provider_name"],
                    gstin=prov["gstin"],
                    provider_id=prov["provider_id"],
                    mcp_endpoint=prov["mcp_endpoint"],
                    confidence=95,
                    metadata=prov["metadata"]
                )

    # 3. Vendor Name match (Priority 3)
    if context.vendor_name:
        vendor_clean = context.vendor_name.strip().lower()
        for prov in MOCK_PROVIDER_REGISTRY:
            prov_name = prov["provider_name"].strip().lower()
            # Direct matches or clear substrings
            if vendor_clean == prov_name or vendor_clean in prov_name or prov_name in vendor_clean:
                logger.info(f"[PROVIDER LOOKUP] Match found via Vendor Name Substring (Priority 3): {prov['provider_name']}")
                return ProviderLookupResult(
                    provider_name=prov["provider_name"],
                    gstin=prov["gstin"],
                    provider_id=prov["provider_id"],
                    mcp_endpoint=prov["mcp_endpoint"],
                    confidence=85,
                    metadata=prov["metadata"]
                )

    logger.warning(f"[PROVIDER LOOKUP] No match found. Returning AMBIGUOUS.")
    return None
