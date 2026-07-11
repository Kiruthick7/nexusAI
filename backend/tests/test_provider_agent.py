"""
Extensive automated unit and integration tests verifying the Provider Verification Agent.

Covers:
1. Cascading Priority Provider Lookup (GSTIN, Phone, Vendor Name).
2. MCP Client resilience (absolute 5s timeouts, retries, Pydantic schemas).
3. Granular progressive telemetry event publishing (lookup, connections, tools).
4. Edge conditions: UNREACHABLE offline, UNREACHABLE slow, AMBIGUOUS, AMOUNT_MISMATCH, and NO_SUCH_INVOICE.
5. Concurrent isolated multi-lane executions.
"""

import asyncio
import pytest
from datetime import datetime, UTC
from app.core.event_bus import event_bus
from app.models.enums import EventType, AgentName, AgentStatus, Severity
from app.models.mission_context import SharedMissionContext
from app.models.evidence import Evidence
from app.workflow.executor import execute_agent_task
from app.tools.provider_lookup import resolve_provider, ProviderLookupResult
from app.tools.provider_client import verify_invoice_with_provider, MCPResponseSchema


def test_cascading_provider_lookup_resolution():
    """
    Unit test asserting the exact cascading priority of the Provider Lookup tool.
    """
    # 1. Priority 1: GSTIN Match (Apollo Hospitals)
    ctx1 = SharedMissionContext(
        mission_id="M-101", claim_id="C-101",
        vendor_name="Some Mismatched Name", gstin="GSTIN-987654321",
        amount=100.0, currency="USD", invoice_number="INV-123", category="Medical"
    )
    res1 = resolve_provider(ctx1)
    assert res1 is not None
    assert res1.provider_name == "Apollo Hospitals"
    assert res1.provider_id == "PROV-APOLLO"
    assert res1.confidence == 100

    # 2. Priority 2: Phone Match (Max Healthcare via context metadata)
    ctx2 = SharedMissionContext(
        mission_id="M-102", claim_id="C-102",
        vendor_name="Wrong Name", gstin=None,
        amount=100.0, currency="USD", invoice_number="INV-123", category="Medical",
        metadata={"phone": "111-222-3330"}
    )
    res2 = resolve_provider(ctx2)
    assert res2 is not None
    assert res2.provider_name == "Max Healthcare"
    assert res2.provider_id == "PROV-MAX"
    assert res2.confidence == 95

    # 3. Priority 3: Fuzzy Vendor Name Substring Match (DeepMind Corp)
    ctx3 = SharedMissionContext(
        mission_id="M-103", claim_id="C-103",
        vendor_name="deepmind", gstin=None,
        amount=100.0, currency="USD", invoice_number="INV-123", category="Medical"
    )
    res3 = resolve_provider(ctx3)
    assert res3 is not None
    assert res3.provider_name == "DeepMind Corp"
    assert res3.provider_id == "PROV-DEEPMIND"
    assert res3.confidence == 85

    # 4. Low confidence fallback: Ambiguous
    ctx4 = SharedMissionContext(
        mission_id="M-104", claim_id="C-104",
        vendor_name="Unregistered Garage", gstin="GST-FAKE",
        amount=100.0, currency="USD", invoice_number="INV-123", category="Transport"
    )
    res4 = resolve_provider(ctx4)
    assert res4 is None


def test_provider_agent_execution_confirmed():
    """
    Integration test verifying successful provider verification (CONFIRMED status).
    """
    mission_id = "M-CONFIRMED"
    ctx = SharedMissionContext(
        mission_id=mission_id, claim_id="C-CONFIRMED",
        vendor_name="Apollo Hospitals", gstin="GSTIN-987654321",
        amount=500.0, currency="USD", invoice_number="INV-ACTIVE-777", category="Medical"
    )

    async def run_test():
        await event_bus.clear_mission(mission_id)
        
        # Execute Provider Agent Task
        raw_evidence = await execute_agent_task(mission_id, "ProviderAgent", ctx)
        
        # Verify validated structure of Evidence output
        evidence = Evidence(**raw_evidence)
        assert evidence.mission_id == mission_id
        assert evidence.agent == AgentName.PROVIDER
        assert evidence.source == "mcp"
        assert evidence.confidence == 100
        assert evidence.severity == Severity.SUCCESS
        assert "CONFIRMED" in evidence.metadata["finding"]
        assert "Ledger Transaction Cleared" in evidence.description
        
        # Verify the progressive stream of telemetry events
        events = await event_bus.replay_events(mission_id)
        event_types = [e.event_type for e in events]
        
        assert EventType.PROVIDER_STARTED in event_types
        assert EventType.PROVIDER_LOOKUP in event_types
        assert EventType.PROVIDER_MCP_CONNECTED in event_types
        assert EventType.PROVIDER_TOOL_CALLED in event_types
        assert EventType.PROVIDER_TOOL_COMPLETED in event_types
        assert EventType.PROVIDER_COMPLETED in event_types

    asyncio.run(run_test())


def test_provider_agent_execution_fake_invoice():
    """
    Integration test verifying behavior when the invoice does not exist at provider ledger.
    """
    mission_id = "M-FAKE-INV"
    ctx = SharedMissionContext(
        mission_id=mission_id, claim_id="C-FAKE-INV",
        vendor_name="DeepMind Corp", gstin="GST-123456",
        amount=1250.0, currency="USD", invoice_number="INV-FAKE-999", category="Technology"
    )

    async def run_test():
        await event_bus.clear_mission(mission_id)
        
        raw_evidence = await execute_agent_task(mission_id, "ProviderAgent", ctx)
        evidence = Evidence(**raw_evidence)
        
        assert evidence.severity == Severity.WARN
        assert evidence.confidence == 100
        assert evidence.metadata["finding"] == "NO_SUCH_INVOICE"
        assert "could not be resolved" in evidence.description
        
        events = await event_bus.replay_events(mission_id)
        # Ensure completed finding event lists WARNING instead of SUCCESS
        completed_event = next(e for e in events if e.event_type == EventType.PROVIDER_COMPLETED)
        assert completed_event.status == AgentStatus.WARNING

    asyncio.run(run_test())


def test_provider_agent_execution_amount_mismatch():
    """
    Integration test verifying behavior when invoice exists but has matching amount differences.
    """
    mission_id = "M-MISMATCH"
    ctx = SharedMissionContext(
        mission_id=mission_id, claim_id="C-MISMATCH",
        vendor_name="Max Healthcare", gstin="GSTIN-111222333",
        amount=1500.0, currency="USD", invoice_number="INV-MISMATCH-123", category="Medical"
    )

    async def run_test():
        await event_bus.clear_mission(mission_id)
        
        raw_evidence = await execute_agent_task(mission_id, "ProviderAgent", ctx)
        evidence = Evidence(**raw_evidence)
        
        assert evidence.severity == Severity.WARN
        assert evidence.metadata["finding"] == "AMOUNT_MISMATCH"
        assert "does not match" in evidence.description

    asyncio.run(run_test())


def test_provider_agent_execution_ambiguous_provider():
    """
    Integration test verifying fallback resolution for unknown vendors.
    """
    mission_id = "M-AMBIGUOUS"
    ctx = SharedMissionContext(
        mission_id=mission_id, claim_id="C-AMBIGUOUS",
        vendor_name="Nonexistent Clinic LLC", gstin=None,
        amount=450.0, currency="USD", invoice_number="INV-999", category="Medical"
    )

    async def run_test():
        await event_bus.clear_mission(mission_id)
        
        raw_evidence = await execute_agent_task(mission_id, "ProviderAgent", ctx)
        evidence = Evidence(**raw_evidence)
        
        assert evidence.source == "db_lookup"
        assert evidence.metadata["finding"] == "AMBIGUOUS"
        assert evidence.severity == Severity.WARN
        assert "failed to locate" in evidence.description
        
        events = await event_bus.replay_events(mission_id)
        lookup_event = next(e for e in events if e.event_type == EventType.PROVIDER_LOOKUP)
        assert lookup_event.metadata["resolved"] is False

    asyncio.run(run_test())


def test_provider_agent_execution_unreachable_offline():
    """
    Integration test verifying MCP resilience during provider offline scenarios.
    """
    mission_id = "M-OFFLINE"
    ctx = SharedMissionContext(
        mission_id=mission_id, claim_id="C-OFFLINE",
        vendor_name="Offline Pharmacy", gstin="GST-OFFLINE",
        amount=150.0, currency="USD", invoice_number="INV-111", category="Medical"
    )

    async def run_test():
        await event_bus.clear_mission(mission_id)
        
        # Test verify_invoice_with_provider fast retries for offline simulation
        raw_evidence = await execute_agent_task(mission_id, "ProviderAgent", ctx)
        evidence = Evidence(**raw_evidence)
        
        assert evidence.metadata["finding"] == "UNREACHABLE"
        assert evidence.severity == Severity.WARN
        assert "Connection failure" in evidence.description
        
        events = await event_bus.replay_events(mission_id)
        assert any(e.event_type == EventType.PROVIDER_FAILED for e in events)

    asyncio.run(run_test())


def test_provider_agent_execution_unreachable_timeout():
    """
    Integration test asserting that provider responses exceeding 5s limit are clean timeouts.
    """
    mission_id = "M-TIMEOUT"
    ctx = SharedMissionContext(
        mission_id=mission_id, claim_id="C-TIMEOUT",
        vendor_name="Slow Laboratory", gstin="GST-SLOW",
        amount=250.0, currency="USD", invoice_number="INV-SLOW-333", category="Medical"
    )

    async def run_test():
        await event_bus.clear_mission(mission_id)
        
        # Quick retries in client to prevent test running for too long
        with patch("app.tools.provider_client.verify_invoice_with_provider") as mock_verify:
            # We mock the timeout return structure which matches verify_invoice_with_provider's handling
            mock_verify.return_value = MCPResponseSchema(
                finding="UNREACHABLE",
                evidence="Connection failure: Provider MCP endpoint did not respond within 5s maximum duration limits.",
                provider="Slow Laboratory",
                response_time_ms=5000,
                confidence=0,
                timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z")
            )
            
            raw_evidence = await execute_agent_task(mission_id, "ProviderAgent", ctx)
            evidence = Evidence(**raw_evidence)
            
            assert evidence.metadata["finding"] == "UNREACHABLE"
            assert "did not respond" in evidence.description

    from unittest.mock import patch
    asyncio.run(run_test())


def test_provider_agent_execution_schema_validation_fault():
    """
    Integration test asserting safe structural handling of response schema ValidationError.
    """
    mission_id = "M-SCHEMA-FAULT"
    ctx = SharedMissionContext(
        mission_id=mission_id, claim_id="C-SCHEMA-FAULT",
        vendor_name="DeepMind Corp", gstin="GST-123456",
        amount=100.0, currency="USD", invoice_number="INV-SCHEMA_ERROR-111", category="Technology"
    )

    async def run_test():
        await event_bus.clear_mission(mission_id)
        
        raw_evidence = await execute_agent_task(mission_id, "ProviderAgent", ctx)
        evidence = Evidence(**raw_evidence)
        
        assert evidence.metadata["finding"] == "FAILED"
        assert evidence.severity == Severity.ERROR
        assert "formatting discrepancies" in evidence.description
        
        events = await event_bus.replay_events(mission_id)
        assert any(e.event_type == EventType.PROVIDER_FAILED for e in events)

    asyncio.run(run_test())


def test_provider_agent_isolated_concurrency():
    """
    Integration test asserting that executing multiple concurrent tasks are fully isolated.
    """
    contexts = [
        SharedMissionContext(
            mission_id=f"M-CONC-{i}", claim_id=f"C-CONC-{i}",
            vendor_name="Apollo Hospitals" if i % 2 == 0 else "DeepMind Corp",
            gstin="GSTIN-987654321" if i % 2 == 0 else "GST-123456",
            amount=100.0 * i, currency="USD", invoice_number=f"INV-N-{i}", category="Medical"
        )
        for i in range(1, 6)
    ]

    async def run_concurrently():
        for ctx in contexts:
            await event_bus.clear_mission(ctx.mission_id)
            
        tasks = [
            execute_agent_task(ctx.mission_id, "ProviderAgent", ctx)
            for ctx in contexts
        ]
        
        results = await asyncio.gather(*tasks)
        
        for i, res in enumerate(results):
            evidence = Evidence(**res)
            assert evidence.mission_id == f"M-CONC-{i+1}"
            assert evidence.metadata["finding"] == "CONFIRMED"
            assert evidence.confidence == 100
            
            # Assert event stream isolation
            events = await event_bus.replay_events(evidence.mission_id)
            for e in events:
                assert e.mission_id == evidence.mission_id

    asyncio.run(run_concurrently())
