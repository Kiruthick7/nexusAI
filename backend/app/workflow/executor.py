"""
Module implementing the monitoring and execution of specialist agent tasks.
Currently executes high-fidelity placeholder workers representing Provider, Policy, and Pattern agents.
"""

import asyncio
import uuid
from datetime import datetime, UTC
from typing import Dict, Any
from app.models.enums import AgentName, EventType, AgentStatus, Severity
from app.core.event_publisher import (
    publish_agent_started,
    publish_agent_completed,
    publish_provider_lookup,
    publish_provider_mcp_connected,
    publish_provider_tool_called,
    publish_provider_tool_completed,
    publish_provider_failed,
    publish_policy_failed,
    publish_pattern_failed,
)
from app.models.mission_context import SharedMissionContext
from app.tools.provider_lookup import resolve_provider
from app.tools.provider_client import verify_invoice_with_provider
from app.models.evidence import Evidence
from app.policy.evaluator import policy_evaluator
from app.pattern.engine import pattern_evaluator
from app.core.logger import logger


async def execute_agent_task(mission_id: str, agent_name: str, context: SharedMissionContext) -> Dict[str, Any]:
    """
    Simulates the asynchronous execution of a specialized agent task with realistic latencies and payloads.
    
    Args:
        mission_id: The active running mission identifier.
        agent_name: The name of the target agent (e.g. 'ProviderAgent', 'PolicyAgent', 'PatternAgent').
        context: The extracted SharedMissionContext facts.
        
    Returns:
        Dict: Structured result metadata of the evaluation.
    """
    if agent_name == "ProviderAgent":
        # 1. Dispatch Provider verification check
        await publish_agent_started(
            mission_id=mission_id,
            agent=AgentName.PROVIDER,
            event_type=EventType.PROVIDER_STARTED,
            title="Provider Verification Started",
            message="Validating healthcare/retail vendor registration and regulatory compliance status"
        )
        
        start_time = datetime.now(UTC)
        
        # 2. Priority Cascading Provider Lookup
        lookup_result = resolve_provider(context)
        
        if not lookup_result:
            # Low confidence or unregistered fallback: return AMBIGUOUS
            await publish_provider_lookup(
                mission_id=mission_id,
                provider_name=context.vendor_name or "Unknown Vendor",
                gstin=context.gstin,
                resolved=False,
                confidence=30
            )
            
            evidence = Evidence(
                evidence_id=str(uuid.uuid4()),
                mission_id=mission_id,
                agent=AgentName.PROVIDER,
                source="db_lookup",
                title="Provider Lookup: Ambiguous",
                description=f"Cascading registry search failed to locate registered partner matching vendor name '{context.vendor_name or 'Unknown'}' or GSTIN '{context.gstin or 'None'}'.",
                confidence=30,
                severity=Severity.WARN,
                timestamp=datetime.now(UTC),
                metadata={
                    "finding": "AMBIGUOUS",
                    "vendor_name": context.vendor_name,
                    "gstin": context.gstin
                }
            )
            
            elapsed_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            await publish_agent_completed(
                mission_id=mission_id,
                agent=AgentName.PROVIDER,
                event_type=EventType.PROVIDER_COMPLETED,
                status=AgentStatus.WARNING,
                title="Provider Lookup Unresolved",
                message=evidence.description,
                severity=Severity.WARN,
                confidence=30,
                latency_ms=elapsed_ms,
                metadata=evidence.metadata
            )
            return evidence.model_dump()

        # Success: Resolved provider registry match
        await publish_provider_lookup(
            mission_id=mission_id,
            provider_name=lookup_result.provider_name,
            gstin=lookup_result.gstin,
            resolved=True,
            confidence=lookup_result.confidence,
            metadata=lookup_result.metadata
        )
        
        # 3. Securely Connect to Provider MCP Tunnel
        await publish_provider_mcp_connected(
            mission_id=mission_id,
            provider_name=lookup_result.provider_name,
            endpoint=lookup_result.mcp_endpoint
        )
        
        # 4. Trigger Provider Ledger Verification Tool
        invoice_number = context.invoice_number or "INV-UNKNOWN"
        amount = context.amount or 0.0
        
        tool_args = {
            "invoice_number": invoice_number,
            "amount": amount,
            "vendor_name": lookup_result.provider_name
        }
        
        await publish_provider_tool_called(
            mission_id=mission_id,
            provider_name=lookup_result.provider_name,
            tool_name="verify_invoice_registration",
            args=tool_args
        )
        
        try:
            # Query Provider endpoint with built-in retries and 5-second limits
            mcp_response = await verify_invoice_with_provider(
                endpoint=lookup_result.mcp_endpoint,
                invoice_number=invoice_number,
                amount=amount,
                vendor_name=lookup_result.provider_name
            )
            
            elapsed_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            
            # Map findings to visual severities and statuses
            if mcp_response.finding == "CONFIRMED":
                status = AgentStatus.SUCCESS
                severity = Severity.SUCCESS
                title = "Provider Verification Cleared"
            elif mcp_response.finding == "UNREACHABLE":
                status = AgentStatus.WARNING
                severity = Severity.WARN
                title = "Provider Endpoint Unreachable"
                # Publish failure telemetry
                await publish_provider_failed(
                    mission_id=mission_id,
                    provider_name=lookup_result.provider_name,
                    error_message=mcp_response.evidence,
                    latency_ms=elapsed_ms
                )
            else:
                status = AgentStatus.WARNING
                severity = Severity.WARN
                title = f"Provider Check: {mcp_response.finding}"
                
            # Publish progressive tool execution closure update
            await publish_provider_tool_completed(
                mission_id=mission_id,
                provider_name=lookup_result.provider_name,
                tool_name="verify_invoice_registration",
                finding=mcp_response.finding,
                latency_ms=elapsed_ms,
                metadata=mcp_response.model_dump()
            )
            
            # Build unified evidence instance
            evidence = Evidence(
                evidence_id=str(uuid.uuid4()),
                mission_id=mission_id,
                agent=AgentName.PROVIDER,
                source="mcp",
                title=title,
                description=mcp_response.evidence,
                confidence=mcp_response.confidence,
                severity=severity,
                timestamp=datetime.now(UTC),
                metadata=mcp_response.model_dump()
            )
            
            await publish_agent_completed(
                mission_id=mission_id,
                agent=AgentName.PROVIDER,
                event_type=EventType.PROVIDER_COMPLETED,
                status=status,
                title=title,
                message=evidence.description,
                severity=severity,
                confidence=evidence.confidence,
                latency_ms=elapsed_ms,
                metadata=evidence.metadata
            )
            return evidence.model_dump()
            
        except Exception as err:
            logger.error(f"[PROVIDER AGENT] Exception encountered during MCP execution: {str(err)}", exc_info=True)
            elapsed_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            
            await publish_provider_failed(
                mission_id=mission_id,
                provider_name=lookup_result.provider_name,
                error_message=f"Schema or internal system fault: {str(err)}",
                latency_ms=elapsed_ms
            )
            
            evidence = Evidence(
                evidence_id=str(uuid.uuid4()),
                mission_id=mission_id,
                agent=AgentName.PROVIDER,
                source="mcp",
                title="Provider Agent Schema Fault",
                description=f"Ledger analysis was aborted due to validator formatting discrepancies: {str(err)}",
                confidence=0,
                severity=Severity.ERROR,
                timestamp=datetime.now(UTC),
                metadata={"finding": "FAILED", "error": str(err)}
            )
            
            await publish_agent_completed(
                mission_id=mission_id,
                agent=AgentName.PROVIDER,
                event_type=EventType.PROVIDER_FAILED,
                status=AgentStatus.ERROR,
                title="Provider Verification Failed",
                message=evidence.description,
                severity=Severity.ERROR,
                confidence=0,
                latency_ms=elapsed_ms,
                metadata=evidence.metadata
            )
            return evidence.model_dump()

    elif agent_name == "PolicyAgent":
        start_time = datetime.now(UTC)
        await publish_agent_started(
            mission_id=mission_id,
            agent=AgentName.POLICY,
            event_type=EventType.POLICY_STARTED,
            title="Policy Audit Started",
            message="Analyzing transaction against enterprise expense guidelines and coverage thresholds"
        )
        
        try:
            # Run the actual rule engine evaluations
            evidence = await policy_evaluator.evaluate_claim(mission_id, context)
            
            # Map aggregate severity to AgentStatus
            status = AgentStatus.SUCCESS
            if evidence.severity == Severity.ERROR:
                status = AgentStatus.ERROR
            elif evidence.severity == Severity.WARN:
                status = AgentStatus.WARNING
                
            elapsed_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            
            await publish_agent_completed(
                mission_id=mission_id,
                agent=AgentName.POLICY,
                event_type=EventType.POLICY_COMPLETED,
                status=status,
                title="Policy Audit Completed",
                message=evidence.description,
                severity=evidence.severity,
                confidence=evidence.confidence,
                latency_ms=elapsed_ms,
                metadata=evidence.metadata
            )
            return evidence.model_dump()
            
        except Exception as err:
            logger.error(f"[POLICY AGENT] Critical exception during rule evaluation: {str(err)}", exc_info=True)
            elapsed_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            
            await publish_policy_failed(
                mission_id=mission_id,
                error=f"Internal rule parser discrepancy: {str(err)}",
                latency_ms=elapsed_ms
            )
            
            evidence = Evidence(
                evidence_id=str(uuid.uuid4()),
                mission_id=mission_id,
                agent=AgentName.POLICY,
                source="rule_engine",
                title="Policy Engine Failure",
                description=f"Corporate guidelines audit failed due to parsing exception: {str(err)}",
                confidence=0,
                severity=Severity.ERROR,
                timestamp=datetime.now(UTC),
                metadata={"finding": "FAILED", "error": str(err)}
            )
            
            await publish_agent_completed(
                mission_id=mission_id,
                agent=AgentName.POLICY,
                event_type=EventType.POLICY_COMPLETED,
                status=AgentStatus.ERROR,
                title="Policy Check Schema Fault",
                message=evidence.description,
                severity=Severity.ERROR,
                confidence=0,
                latency_ms=elapsed_ms,
                metadata=evidence.metadata
            )
            return evidence.model_dump()

    elif agent_name == "PatternAgent":
        # 3. Dispatch Pattern fraud/duplicate scan
        await publish_agent_started(
            mission_id=mission_id,
            agent=AgentName.PATTERN,
            event_type=EventType.PATTERN_STARTED,
            title="Historical Pattern Scan Started",
            message="Scanning transaction records database for duplicates, split billing anomalies, or frequency violations"
        )
        
        start_time = datetime.now()
        try:
            evidence = await pattern_evaluator.evaluate_patterns(mission_id, context)
            
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            status = AgentStatus.SUCCESS
            if evidence.severity == Severity.WARN:
                status = AgentStatus.WARNING
            elif evidence.severity == Severity.ERROR:
                status = AgentStatus.ERROR

            await publish_agent_completed(
                mission_id=mission_id,
                agent=AgentName.PATTERN,
                event_type=EventType.PATTERN_COMPLETED,
                status=status,
                title=evidence.title,
                message=evidence.description,
                severity=evidence.severity,
                confidence=evidence.confidence,
                latency_ms=latency_ms,
                metadata=evidence.metadata
            )
            return evidence.model_dump()

        except Exception as err:
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"[WORKFLOW EXECUTOR] Pattern Agent evaluation aborted with error: {str(err)}")
            await publish_pattern_failed(mission_id=mission_id, error=str(err), latency_ms=latency_ms)
            raise

    else:
        raise ValueError(f"Unknown executor agent_name '{agent_name}' requested.")
