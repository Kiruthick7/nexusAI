"""
Module implementing the resilient Provider MCP client.

Handles connections to provider endpoints, enforces 5 seconds maximum timeouts,
runs exponential-backoff retry sweeps, and validates structural schemas.
"""

import asyncio
import time
from datetime import datetime, UTC
from typing import Dict, Any
from pydantic import BaseModel, Field, ValidationError
from app.core.logger import logger


class MCPResponseSchema(BaseModel):
    """
    Schema validating standard MCP verification returns.
    """
    finding: str = Field(pattern="^(CONFIRMED|NO_SUCH_INVOICE|AMOUNT_MISMATCH|UNREACHABLE|FAILED)$")
    evidence: str = Field(description="Detailed verification summary from the provider database.")
    provider: str = Field(description="The registered name of the provider.")
    response_time_ms: int = Field(ge=0, description="Verification latency metric.")
    confidence: int = Field(ge=0, le=100, description="Verification accuracy confidence level.")
    timestamp: str = Field(description="ISO-8601 formatted verification timestamp.")


async def verify_invoice_with_provider(
    endpoint: str,
    invoice_number: str,
    amount: float,
    vendor_name: str,
    max_retries: int = 3,
    initial_delay: float = 0.5
) -> MCPResponseSchema:
    """
    Simulates a robust, schema-validated connection to a third-party Provider MCP Server.
    
    Features:
    - strict 5-second absolute timeout limits.
    - Asynchronous exponential-backoff retries.
    - Strict Pydantic response validation.
    """
    logger.debug(f"[MCP CLIENT] Querying endpoint={endpoint} for invoice={invoice_number}, amount={amount}")
    
    delay = initial_delay
    last_err: Optional[Exception] = None
    
    for attempt in range(1, max_retries + 1):
        try:
            start_time = time.perf_counter()
            
            # Enforce strict 5.0 seconds maximum timeout on the async execution
            # Wrap simulated network query within asyncio.wait_for
            response_dict = await asyncio.wait_for(
                _simulate_endpoint_query(endpoint, invoice_number, amount, vendor_name),
                timeout=5.0
            )
            
            end_time = time.perf_counter()
            elapsed_ms = int((end_time - start_time) * 1000)
            
            # Enrich response metrics
            response_dict["response_time_ms"] = elapsed_ms
            
            # Validate schema
            validated_response = MCPResponseSchema(**response_dict)
            logger.info(f"[MCP CLIENT] Successfully verified on attempt {attempt}. Finding={validated_response.finding}")
            return validated_response
            
        except asyncio.TimeoutError as e:
            logger.warning(f"[MCP CLIENT] Attempt {attempt}/{max_retries} timed out (> 5.0s) for endpoint {endpoint}")
            last_err = e
        except ValidationError as e:
            logger.error(f"[MCP CLIENT] Schema validation failure on endpoint {endpoint}: {str(e)}")
            raise e
        except Exception as e:
            logger.warning(f"[MCP CLIENT] Attempt {attempt}/{max_retries} failed on endpoint {endpoint}: {str(e)}")
            last_err = e
            
        if attempt < max_retries:
            logger.debug(f"[MCP CLIENT] Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
            delay *= 2  # Exponential backoff
            
    # All retries failed or timed out
    logger.error(f"[MCP CLIENT] All {max_retries} connection attempts failed. Last error: {str(last_err)}")
    
    # Return UNREACHABLE mock schema fallback conforming to error instructions
    return MCPResponseSchema(
        finding="UNREACHABLE",
        evidence=f"Connection failure: Provider MCP endpoint {endpoint} did not respond within {max_retries} retry loops.",
        provider=vendor_name,
        response_time_ms=5000,
        confidence=0,
        timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )


async def _simulate_endpoint_query(
    endpoint: str,
    invoice_number: str,
    amount: float,
    vendor_name: str
) -> Dict[str, Any]:
    """
    Simulates high-fidelity response configurations representing several provider behaviors.
    """
    # 1. Simulate absolute slow provider (e.g. > 5s timeout)
    if "mcp-slow" in endpoint:
        logger.info("[MCP CLIENT] Simulating slow provider. Sleeping for 6.0 seconds...")
        await asyncio.sleep(6.0)  # Will exceed 5s timeout limits and trigger TimeoutError
        
    # 2. Simulate complete network offline provider
    if "mcp-offline" in endpoint:
        logger.info("[MCP CLIENT] Simulating completely offline provider.")
        raise ConnectionRefusedError(f"Connection refused at host {endpoint}")
        
    # Standard connection delay
    await asyncio.sleep(0.3)
    
    timestamp_str = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    
    # 3. Mismatched amount checks
    if "mcp-mismatch" in endpoint or (invoice_number and "MISMATCH" in invoice_number):
        return {
            "finding": "AMOUNT_MISMATCH",
            "evidence": f"Provider records audit completed: Invoice {invoice_number} found, but registered amount 1.00 USD does not match requested expense of {amount} USD.",
            "provider": vendor_name,
            "confidence": 100,
            "timestamp": timestamp_str
        }
        
    # 4. Non-existent invoice checks
    if invoice_number and ("FAKE" in invoice_number or "BAD" in invoice_number):
        return {
            "finding": "NO_SUCH_INVOICE",
            "evidence": f"Provider ledger audit completed: Invoice registration {invoice_number} could not be resolved or found inside the registered system entries.",
            "provider": vendor_name,
            "confidence": 100,
            "timestamp": timestamp_str
        }
        
    # 5. Schema mismatch simulation trigger
    if invoice_number and "SCHEMA_ERROR" in invoice_number:
        # Returns invalid schema keys to trigger ValidationError
        return {
            "finding": "INVALID_STATUS",  # Will fail pattern constraint
            "evidence": "Fails validation schema",
            "provider": vendor_name,
            "confidence": 200,            # Fails ge=0 le=100 limit
            "timestamp": timestamp_str
        }

    # Default: Confirmed valid transaction
    return {
        "finding": "CONFIRMED",
        "evidence": f"Ledger Transaction Cleared: Invoice registration {invoice_number} matched securely with provider record registries.",
        "provider": vendor_name,
        "confidence": 100,
        "timestamp": timestamp_str
    }
