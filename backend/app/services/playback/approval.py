"""
Module implementing the "Clean Approval" demo playback scenario.

Simulates a perfect adjudication flow where all parallel agents complete with
success status, clearing automated gates to approve the claim.
"""

import asyncio
import random
from app.models.enums import WorkflowStatus, AgentName, AgentStatus, Severity, EventType
from app.core.mission_manager import mission_manager
from app.core.event_publisher import (
    publish_workflow_started,
    publish_agent_started,
    publish_agent_completed,
    publish_gate_check,
    publish_decision,
    publish_workflow_completed,
)


async def run_approval_playback(mission_id: str) -> None:
    """
    Executes the sequential Clean Approval agent simulation.
    """
    async def random_delay() -> None:
        await asyncio.sleep(random.uniform(0.5, 1.5))

    # 1. Intake document scanning
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.INGESTING)
    await mission_manager.update_stage(mission_id, "INGESTING")
    
    # Publish intake started
    await publish_agent_started(
        mission_id,
        agent=None,
        event_type=EventType.INTAKE_STARTED,
        title="Document Ingestion Initiated",
        message="Acquiring med_invoice_101.pdf (1.1 MB) from gateway",
    )
    await random_delay()
    
    # Publish extraction completed
    await publish_agent_completed(
        mission_id,
        agent=None,
        event_type=EventType.EXTRACTION_COMPLETED,
        status=AgentStatus.SUCCESS,
        title="OCR Parsing Completed",
        message="Extracted fields from med_invoice_101.pdf",
        confidence=98,
        metadata={
            "vendor_name": "Aarthi Scans",
            "gstin": "33AABCA1234F1Z0",
            "category": "Medical Scans",
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
        message="Orchestration path compiling",
    )
    await random_delay()
    
    await publish_agent_completed(
        mission_id,
        agent=AgentName.PLANNER,
        event_type=EventType.PLANNER_DISPATCH,
        status=AgentStatus.SUCCESS,
        title="Planning Complete",
        message="Dispatched analysis to parallel nodes",
        tools_used=["get_agent_manifest"],
        metadata={"dispatched_agents": ["ProviderAgent", "PolicyAgent", "PatternAgent"]}
    )
    await random_delay()

    # 3. Parallel Audits
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.ANALYZING)
    await mission_manager.update_stage(mission_id, "ANALYZING")
    
    # Provider checks
    await publish_agent_started(
        mission_id,
        agent=AgentName.PROVIDER,
        event_type=EventType.PROVIDER_STARTED,
        title="ProviderAgent Audit Initialized",
        message="Verifying medical credentials and active licensing boards",
    )
    await random_delay()
    await publish_agent_completed(
        mission_id,
        agent=AgentName.PROVIDER,
        event_type=EventType.PROVIDER_COMPLETED,
        status=AgentStatus.SUCCESS,
        title="Provider Check Completed",
        message="Provider registered, licensing verified valid",
        confidence=99,
        tools_used=["validate_gstin", "check_medical_registry"]
    )
    await random_delay()

    # Policy checks
    await publish_agent_started(
        mission_id,
        agent=AgentName.POLICY,
        event_type=EventType.POLICY_STARTED,
        title="PolicyAgent Guideline Audit Initialized",
        message="Cross-referencing invoice line items with enterprise rules",
    )
    await random_delay()
    await publish_agent_completed(
        mission_id,
        agent=AgentName.POLICY,
        event_type=EventType.POLICY_COMPLETED,
        status=AgentStatus.SUCCESS,
        title="Policy Check Completed",
        message="Invoice amount fits corporate limits, no exceptions found",
        confidence=97,
        tools_used=["evaluate_limits_model"]
    )
    await random_delay()

    # Pattern checks
    await publish_agent_started(
        mission_id,
        agent=AgentName.PATTERN,
        event_type=EventType.PATTERN_STARTED,
        title="PatternAgent Duplicate Audit Initialized",
        message="Scanning claim hashes in historical transactions registry",
    )
    await random_delay()
    await publish_agent_completed(
        mission_id,
        agent=AgentName.PATTERN,
        event_type=EventType.PATTERN_COMPLETED,
        status=AgentStatus.SUCCESS,
        title="Pattern Check Completed",
        message="Historical database match clear. No duplicate anomalies found",
        confidence=99,
        tools_used=["calculate_claim_hash", "fuzzy_invoice_matcher"]
    )
    await random_delay()

    # 4. Arbitration & Gates
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.ARBITRATING)
    await mission_manager.update_stage(mission_id, "ARBITRATING")
    
    await publish_gate_check(
        mission_id,
        title="Automated Policy Gate: APPROVED",
        message="All parallel agents returned SUCCESS. No manual review required.",
        cleared=True
    )
    await random_delay()

    # 5. Completion & Decision
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.COMPLETED)
    await mission_manager.update_stage(mission_id, "COMPLETED")
    
    await publish_decision(
        mission_id,
        decision_status="APPROVED",
        subtext="PASSED POLICY LIMITS",
        title="Adjudication Decided",
        message="Expense claim fully cleared and approved",
        severity=Severity.SUCCESS,
        latency_ms=4500,
        metadata={"processed_by": "NexusCore-v1"}
    )
    await random_delay()
    
    await publish_workflow_completed(
        mission_id,
        title="Workflow Finalized",
        message="Mission completed successfully in 4.5 seconds"
    )
