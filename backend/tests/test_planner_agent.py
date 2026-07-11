"""
Comprehensive automated unit and integration tests verifying the modular Planner Agent orchestration engine.
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from app.core.mission_manager import mission_manager
from app.core.event_bus import event_bus
from app.models.enums import EventType, AgentName, AgentStatus, Severity, WorkflowStatus
from app.models.mission_context import SharedMissionContext
from app.models.evidence import Evidence
from app.workflow.graph import WorkflowGraph
from app.workflow.dispatcher import WorkflowDispatcher
from app.workflow.executor import execute_agent_task
from app.workflow.planner import run_planner_agent


def test_topological_graph_compilation_and_cycle_checking():
    """
    Unit test verifying Kahn-style topological layer sorting and cycle detection safety.
    """
    # 1. Valid acyclic graph
    graph = WorkflowGraph()
    graph.add_node("PlannerAgent", dependencies=[])
    graph.add_node("ProviderAgent", dependencies=["PlannerAgent"])
    graph.add_node("PolicyAgent", dependencies=["PlannerAgent"])
    graph.add_node("PatternAgent", dependencies=["PlannerAgent"])
    graph.add_node("ArbiterAgent", dependencies=["ProviderAgent", "PolicyAgent", "PatternAgent"])
    
    layers = graph.get_parallel_groups()
    
    assert len(layers) == 3
    assert layers[0] == ["PlannerAgent"]
    assert sorted(layers[1]) == ["PatternAgent", "PolicyAgent", "ProviderAgent"]
    assert layers[2] == ["ArbiterAgent"]
    
    # 2. Invalid cyclic graph (should fail topological sorting)
    cyclic_graph = WorkflowGraph()
    cyclic_graph.add_node("A", dependencies=["C"])
    cyclic_graph.add_node("B", dependencies=["A"])
    cyclic_graph.add_node("C", dependencies=["B"])
    
    with pytest.raises(ValueError, match="Circular dependency detected"):
        cyclic_graph.get_parallel_groups()


def test_executor_specialist_workers_simulated_outputs():
    """
    Unit test verifying that specialist placeholder workers dynamically evaluate facts and publish correct events.
    """
    mission_id = "TEST-EXE-101"
    
    context = SharedMissionContext(
        mission_id=mission_id,
        claim_id="CLAIM-EXE-101",
        vendor_name="DeepMind Corp",
        gstin="GST-123456",
        amount=12500.0,
        currency="INR",
        invoice_number="INV-10023",
        category="Technology",
        raw_ocr_text="Sample OCR content",
        confidence={}
    )
    
    async def run_executor_checks():
        # Clear EventBus first
        await event_bus.clear_mission(mission_id)
        
        # Patch PolicyAgent evaluator call to keep planner loop checks isolated and deterministic
        with patch("app.workflow.executor.policy_evaluator.evaluate_claim") as mock_eval:
            mock_eval.return_value = Evidence(
                evidence_id="POL-MOCK-01",
                mission_id=mission_id,
                agent=AgentName.POLICY,
                source="rule_engine",
                title="Policy Audit Completed",
                description="Audit warning: Expensed amount 12500.0 INR exceeds corporate standard limit of 5000.",
                confidence=95,
                severity=Severity.WARN,
                timestamp=datetime.now(UTC),
                metadata={"finding": "WARNING"}
            )
            
            # 1. Run Provider Check (with active GSTIN -> should be success)
            res_provider = await execute_agent_task(mission_id, "ProviderAgent", context)
            assert res_provider["severity"] == Severity.SUCCESS
            assert "INV-10023" in res_provider["description"]
            
            # 2. Run Policy Check (with amount > 5000 -> should warn)
            res_policy = await execute_agent_task(mission_id, "PolicyAgent", context)
            assert res_policy["severity"] == Severity.WARN
            assert "exceeds corporate standard limit" in res_policy["description"]
            
            # 3. Run Pattern Check (with duplicate invoice number -> should error)
            res_pattern = await execute_agent_task(mission_id, "PatternAgent", context)
            assert res_pattern["severity"] == Severity.ERROR
            assert "Duplicate transaction detected" in res_pattern["description"]
            
            # Verify events were published to the bus
            events = await event_bus.replay_events(mission_id)
            event_types = [e.event_type for e in events]
            
            assert len(events) >= 10
            assert EventType.PROVIDER_STARTED in event_types
            assert EventType.PROVIDER_COMPLETED in event_types
            assert EventType.POLICY_STARTED in event_types
            assert EventType.POLICY_COMPLETED in event_types
            assert EventType.PATTERN_STARTED in event_types
            assert EventType.PATTERN_COMPLETED in event_types

    from datetime import datetime, UTC
    asyncio.run(run_executor_checks())


def test_planner_agent_orchestration_flow_and_telemetry():
    """
    Integration test verifying the end-to-end execution of run_planner_agent.
    """
    mission_id = "TEST-PLAN-999"
    claim_id = "CLAIM-NEX-999"
    
    context = SharedMissionContext(
        mission_id=mission_id,
        claim_id=claim_id,
        vendor_name="Apollo Hospitals",
        gstin="GSTIN-987654321",
        amount=420.50,
        currency="USD",
        invoice_number="INV-NORMAL",
        category="Travel",
        date="2026-07-01",
        raw_ocr_text="Healthcare Receipt OCR",
        confidence={}
    )
    
    async def run_planner_checks():
        # Clean state in registries
        await mission_manager.clear_mission(mission_id)
        await event_bus.clear_mission(mission_id)
        
        # Create mission
        await mission_manager.create_mission(mission_id, claim_id)
        
        # Run Planner Agent (in mock fallback mode)
        plan = await run_planner_agent(mission_id, claim_id, context)
        
        # 1. Assert plan compilation details
        assert plan.mission_id == mission_id
        assert sorted(plan.participating_agents) == ["PatternAgent", "PolicyAgent", "ProviderAgent"]
        assert plan.current_status == "completed"
        
        # 2. Assert mission state mutations in MissionManager
        mission = await mission_manager.get_mission(mission_id)
        assert mission is not None
        assert mission.workflow_status == WorkflowStatus.COMPLETED
        assert mission.current_stage == "COMPLETED"
        assert "agent_results" in mission.metadata
        
        # Check collected agent outputs inside metadata
        results = mission.metadata["agent_results"]
        assert "ProviderAgent" in results
        assert "PolicyAgent" in results
        assert "PatternAgent" in results
        
        # Normal bounds should result in Provider=success, Policy=success, Pattern=success
        assert results["ProviderAgent"]["severity"] == Severity.SUCCESS
        assert "CONFIRMED" in results["ProviderAgent"]["metadata"]["finding"]
        assert results["PolicyAgent"]["severity"] == Severity.SUCCESS
        assert results["PatternAgent"]["severity"] == Severity.SUCCESS
        
        # 3. Assert correct sequential event logging in EventBus history
        events = await event_bus.replay_events(mission_id)
        event_types = [e.event_type for e in events]
        
        # Core expected checkpoints:
        # - planner_started
        # - planner_dispatch
        # - (parallel lanes: provider_started/completed, policy_started/completed, pattern_started/completed)
        # - workflow_completed
        assert EventType.PLANNER_STARTED in event_types
        assert EventType.PLANNER_DISPATCH in event_types
        assert EventType.PROVIDER_STARTED in event_types
        assert EventType.PROVIDER_COMPLETED in event_types
        assert EventType.POLICY_STARTED in event_types
        assert EventType.POLICY_COMPLETED in event_types
        assert EventType.PATTERN_STARTED in event_types
        assert EventType.PATTERN_COMPLETED in event_types
        assert EventType.WORKFLOW_COMPLETED in event_types

    asyncio.run(run_planner_checks())
