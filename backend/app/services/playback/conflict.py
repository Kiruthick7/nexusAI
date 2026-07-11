"""
Module implementing the "Conflict + Escalation" demo playback scenario.

Simulates a policy exception scenario where PolicyAgent flags an Out of Network
medical limits warning, escalating to ArbiterAgent and ultimately human verification.
"""

import asyncio
import random
from app.models.enums import WorkflowStatus, AgentName, AgentStatus, Severity, EventType
from app.core.mission_manager import mission_manager
from app.core.event_publisher import (
    publish_workflow_started,
    publish_agent_started,
    publish_agent_completed,
    publish_conflict,
    publish_decision,
    publish_workflow_completed,
)


async def run_conflict_playback(mission_id: str) -> None:
    """
    Executes the sequential Conflict & Escalation audit simulation.
    """
    async def random_delay() -> None:
        await asyncio.sleep(random.uniform(0.5, 1.5))

    # 1. Intake
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.INGESTING)
    await mission_manager.update_stage(mission_id, "INGESTING")
    
    await publish_agent_started(
        mission_id,
        agent=None,
        event_type=EventType.INTAKE_STARTED,
        title="Document Ingestion Initiated",
        message="Acquiring dental_invoice_04.pdf (850 KB) from gateway",
    )
    await random_delay()
    
    await publish_agent_completed(
        mission_id,
        agent=None,
        event_type=EventType.EXTRACTION_COMPLETED,
        status=AgentStatus.SUCCESS,
        title="OCR Parsing Completed",
        message="Extracted fields from dental_invoice_04.pdf",
        confidence=95,
        metadata={
            "vendor_name": "Precision Dental",
            "category": "Dental Care",
        }
    )
    await random_delay()

    # 2. Planning
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.PLANNING)
    await mission_manager.update_stage(mission_id, "PLANNING")
    await publish_agent_started(
        mission_id,
        agent=AgentName.PLANNER,
        event_type=EventType.PLANNER_STARTED,
        title="Planner Activated",
        message="Calculating analysis channels",
    )
    await random_delay()
    await publish_agent_completed(
        mission_id,
        agent=AgentName.PLANNER,
        event_type=EventType.PLANNER_DISPATCH,
        status=AgentStatus.SUCCESS,
        title="Planner Completed",
        message="Dispatched analysis tasks to parallel nodes",
        metadata={"dispatched_agents": ["ProviderAgent", "PolicyAgent", "PatternAgent"]}
    )
    await random_delay()

    # 3. Parallel Audits
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.ANALYZING)
    await mission_manager.update_stage(mission_id, "ANALYZING")
    
    # Provider
    await publish_agent_started(
        mission_id,
        agent=AgentName.PROVIDER,
        event_type=EventType.PROVIDER_STARTED,
        title="ProviderAgent Initialized",
        message="Verifying dental practice license registry",
    )
    await random_delay()
    await publish_agent_completed(
        mission_id,
        agent=AgentName.PROVIDER,
        event_type=EventType.PROVIDER_COMPLETED,
        status=AgentStatus.SUCCESS,
        title="Provider Check Completed",
        message="Dental license verified active",
        confidence=98,
    )
    await random_delay()

    # Policy (Warning triggered!)
    await publish_agent_started(
        mission_id,
        agent=AgentName.POLICY,
        event_type=EventType.POLICY_STARTED,
        title="PolicyAgent Initialized",
        message="Evaluating insurance coverage guidelines",
    )
    await random_delay()
    await publish_agent_completed(
        mission_id,
        agent=AgentName.POLICY,
        event_type=EventType.POLICY_COMPLETED,
        status=AgentStatus.WARNING,
        title="Policy Exception Detected",
        message="Dental clinic detected Out of Network. Requires co-pay adjustments.",
        severity=Severity.WARN,
        confidence=91,
    )
    await random_delay()

    # Pattern
    await publish_agent_started(
        mission_id,
        agent=AgentName.PATTERN,
        event_type=EventType.PATTERN_STARTED,
        title="PatternAgent Initialized",
        message="Scanning claim hashes in historical transactions",
    )
    await random_delay()
    await publish_agent_completed(
        mission_id,
        agent=AgentName.PATTERN,
        event_type=EventType.PATTERN_COMPLETED,
        status=AgentStatus.SUCCESS,
        title="Pattern Check Completed",
        message="No matching duplicate invoices found",
        confidence=99,
    )
    await random_delay()

    # 4. Arbitration
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.ARBITRATING)
    await mission_manager.update_stage(mission_id, "ARBITRATING")
    
    await publish_conflict(
        mission_id,
        title="Unresolved Boundary Exception",
        message="Out of network medical limits exception raised. Routing to Arbiter.",
        severity=Severity.WARN,
        agent=AgentName.ARBITER
    )
    await random_delay()

    await publish_agent_started(
        mission_id,
        agent=AgentName.ARBITER,
        event_type=EventType.ARBITER_STARTED,
        title="ArbiterAgent Activated",
        message="Assessing co-pay exception rules...",
    )
    await random_delay()
    
    await publish_agent_completed(
        mission_id,
        agent=AgentName.ARBITER,
        event_type=EventType.ARBITER_COMPLETED,
        status=AgentStatus.WARNING,
        title="Arbiter Check Completed",
        message="Exception validated. Escalation required: Out of Network requires human approval override.",
        severity=Severity.WARN
    )
    await random_delay()

    # Trigger Human Override Required
    await publish_agent_started(
        mission_id,
        agent=None,
        event_type=EventType.HUMAN_REQUIRED,
        title="Human Gate Triggered",
        message="Manual claim processor verification required for Out-of-Network exception override.",
    )
    await random_delay()

    # 5. Completion & Decision
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.COMPLETED)
    await mission_manager.update_stage(mission_id, "COMPLETED")
    
    await publish_decision(
        mission_id,
        decision_status="ESCALATED",
        subtext="OUT OF NETWORK EXCEPTION",
        title="Adjudication Escalated",
        message="Claim escalated. Human review gate pending.",
        severity=Severity.WARN,
        latency_ms=5100,
    )
    await random_delay()
    
    await publish_workflow_completed(
        mission_id,
        title="Workflow Finalized",
        message="Mission completed with escalation state"
    )
