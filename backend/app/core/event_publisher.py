"""
Module declaring unified high-level event-publishing helper triggers.

Wraps EventBus.publish under canonical helper signatures, auto-generating
event IDs, timestamps, and enforcing complete schema validation.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.models.event import Event
from app.models.enums import EventType, AgentName, AgentStatus, Severity
from app.core.event_bus import event_bus


def _create_base_event(
    mission_id: str,
    event_type: EventType,
    title: str,
    message: str,
    severity: Severity,
    agent: Optional[AgentName] = None,
    status: Optional[AgentStatus] = None,
    confidence: Optional[int] = None,
    latency_ms: Optional[int] = None,
    tools_used: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    """
    Private utility building a fully validated Event payload structure.
    """
    return Event(
        event_id=str(uuid.uuid4()),
        mission_id=mission_id,
        event_type=event_type,
        agent=agent,
        status=status,
        title=title,
        message=message,
        severity=severity,
        confidence=confidence,
        latency_ms=latency_ms,
        tools_used=tools_used or [],
        timestamp=datetime.now(timezone.utc),
        metadata=metadata or {},
    )


async def publish_workflow_started(
    mission_id: str,
    title: str = "Workflow Initialized",
    message: str = "Orchestration session initialized",
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    """
    Helper publishing a workflow_started event.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.WORKFLOW_STARTED,
        title=title,
        message=message,
        severity=Severity.INFO,
        metadata=metadata,
    )
    await event_bus.publish(event)
    return event


async def publish_agent_started(
    mission_id: str,
    agent: AgentName,
    event_type: EventType,
    title: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    """
    Helper publishing starting milestones of an agent (e.g. provider_started, policy_started).
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=event_type,
        agent=agent,
        status=AgentStatus.LOADING,
        title=title,
        message=message,
        severity=Severity.INFO,
        metadata=metadata,
    )
    await event_bus.publish(event)
    return event


async def publish_agent_completed(
    mission_id: str,
    agent: AgentName,
    event_type: EventType,
    status: AgentStatus,
    title: str,
    message: str,
    severity: Severity = Severity.SUCCESS,
    confidence: Optional[int] = None,
    latency_ms: Optional[int] = None,
    tools_used: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    """
    Helper publishing final evaluation results of an agent (e.g. pattern_completed).
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=event_type,
        agent=agent,
        status=status,
        title=title,
        message=message,
        severity=severity,
        confidence=confidence,
        latency_ms=latency_ms,
        tools_used=tools_used,
        metadata=metadata,
    )
    await event_bus.publish(event)
    return event


async def publish_conflict(
    mission_id: str,
    title: str,
    message: str,
    severity: Severity = Severity.WARN,
    agent: Optional[AgentName] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    """
    Helper publishing a conflict_detected or human_required anomaly event.
    """
    # Infer EventType from severity or context
    e_type = EventType.HUMAN_REQUIRED if severity == Severity.ERROR else EventType.CONFLICT_DETECTED
    event = _create_base_event(
        mission_id=mission_id,
        event_type=e_type,
        agent=agent,
        status=AgentStatus.PENDING if severity == Severity.WARN else AgentStatus.ERROR,
        title=title,
        message=message,
        severity=severity,
        metadata=metadata,
    )
    await event_bus.publish(event)
    return event


async def publish_gate_check(
    mission_id: str,
    title: str,
    message: str,
    cleared: bool,
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    """
    Helper publishing automated security tool gate check logs.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.GATE_CHECK,
        title=title,
        message=message,
        severity=Severity.SUCCESS if cleared else Severity.WARN,
        metadata={"cleared": cleared, **(metadata or {})},
    )
    await event_bus.publish(event)
    return event


async def publish_decision(
    mission_id: str,
    decision_status: str,
    subtext: str,
    title: str = "Adjudication Decision",
    message: str = "Final claim determination completed",
    severity: Severity = Severity.SUCCESS,
    latency_ms: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    """
    Helper publishing final claim outcome determination events.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.DECISION,
        title=title,
        message=message,
        severity=severity,
        latency_ms=latency_ms,
        metadata={"decision": decision_status, "subtext": subtext, **(metadata or {})},
    )
    await event_bus.publish(event)
    return event


async def publish_workflow_completed(
    mission_id: str,
    title: str = "Workflow Completed",
    message: str = "Mission finalized successfully",
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    """
    Helper publishing absolute mission workflow closure milestones.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.WORKFLOW_COMPLETED,
        title=title,
        message=message,
        severity=Severity.SUCCESS,
        metadata=metadata,
    )
    await event_bus.publish(event)
    return event
