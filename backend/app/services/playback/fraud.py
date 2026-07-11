"""
Module implementing the "Fake Invoice" demo playback scenario.

Simulates a fraudulent transaction audit where PatternAgent detects a 100% duplicate
hash match in historical records, escalating to ArbiterAgent before final rejection.
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


async def run_fraud_playback(mission_id: str) -> None:
    """
    Executes the sequential Fake Invoice fraud detection simulation.
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
        message="Acquiring fake_receipt_99.pdf (450 KB) from gateway",
    )
    await random_delay()
    
    await publish_agent_completed(
        mission_id,
        agent=None,
        event_type=EventType.EXTRACTION_COMPLETED,
        status=AgentStatus.SUCCESS,
        title="OCR Parsing Completed",
        message="Extracted fields from fake_receipt_99.pdf",
        confidence=92,
        metadata={
            "vendor_name": "Apex Consulting",
            "category": "Office Stationery",
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
        message="Evaluating routing directives",
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
        message="Verifying business registration and active board licensing status",
    )
    await random_delay()
    await publish_agent_completed(
        mission_id,
        agent=AgentName.PROVIDER,
        event_type=EventType.PROVIDER_COMPLETED,
        status=AgentStatus.SUCCESS,
        title="Provider Check Completed",
        message="Business status verified active, licensed",
        confidence=95,
    )
    await random_delay()

    # Policy
    await publish_agent_started(
        mission_id,
        agent=AgentName.POLICY,
        event_type=EventType.POLICY_STARTED,
        title="PolicyAgent Initialized",
        message="Verifying corporate spend limits and guidelines",
    )
    await random_delay()
    await publish_agent_completed(
        mission_id,
        agent=AgentName.POLICY,
        event_type=EventType.POLICY_COMPLETED,
        status=AgentStatus.SUCCESS,
        title="Policy Check Completed",
        message="Amount remains within policy boundaries",
        confidence=92,
    )
    await random_delay()

    # Pattern (Duplicate alert!)
    await publish_agent_started(
        mission_id,
        agent=AgentName.PATTERN,
        event_type=EventType.PATTERN_STARTED,
        title="PatternAgent Initialized",
        message="Scanning claim hashes in historical transactions registry",
    )
    await random_delay()
    await publish_agent_completed(
        mission_id,
        agent=AgentName.PATTERN,
        event_type=EventType.PATTERN_COMPLETED,
        status=AgentStatus.ERROR,
        title="Pattern Check: ALERT",
        message="Potential duplicate matching NEX-8102 detected inside historical database",
        confidence=99,
        tools_used=["fuzzy_invoice_matcher"]
    )
    await random_delay()

    # 4. Arbitration
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.ARBITRATING)
    await mission_manager.update_stage(mission_id, "ARBITRATING")
    
    await publish_conflict(
        mission_id,
        title="Conflict Flagged",
        message="High-severity fraud duplicate exception triggered. Invoking ArbiterAgent.",
        severity=Severity.ERROR,
        agent=AgentName.ARBITER
    )
    await random_delay()

    # Arbiter Starts & compiled monospaced streams
    await publish_agent_started(
        mission_id,
        agent=AgentName.ARBITER,
        event_type=EventType.ARBITER_STARTED,
        title="ArbiterAgent Activated",
        message="Acquiring duplicate claim contexts NEX-8102 and comparing file metadata",
    )
    
    # We simulate streaming monospaced logs through metadata parameters so they can render beautifully
    logs = [
        "> Fetching historical claim NEX-8102 from BigQuery...",
        "> Comparing hash signature with local fake_receipt_99.pdf...",
        "> CRITICAL: File hashes match 100%. Exact duplicate detected.",
        "> Metadata check: Created dates differ, but transaction and amounts match exactly.",
        "> [CONCLUSION]: Double-billing fraud sequence verified.",
        "> Escalation state resolved: Fraud check failed. Setting final state: REJECTED"
    ]
    
    for log_line in logs:
        await asyncio.sleep(0.3)
        await publish_agent_completed(
            mission_id,
            agent=AgentName.ARBITER,
            event_type=EventType.ARBITER_COMPLETED,
            status=AgentStatus.ERROR,
            title="Arbiter Compiler",
            message=log_line,
            severity=Severity.ERROR,
            metadata={"logs": logs}
        )

    await random_delay()

    # 5. Completion & Decision
    await mission_manager.update_workflow_status(mission_id, WorkflowStatus.COMPLETED)
    await mission_manager.update_stage(mission_id, "COMPLETED")
    
    await publish_decision(
        mission_id,
        decision_status="REJECTED",
        subtext="FRAUD DUPLICATE MATCH",
        title="Adjudication Rejected",
        message="Expense claim rejected due to duplicate billing risk",
        severity=Severity.ERROR,
        latency_ms=5800,
        metadata={"flag_code": "DB-09"}
    )
    await random_delay()
    
    await publish_workflow_completed(
        mission_id,
        title="Workflow Finalized",
        message="Mission completed with rejection state"
    )
