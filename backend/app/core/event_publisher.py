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


async def publish_field_extracted(
    mission_id: str,
    field_name: str,
    field_value: Any,
    confidence_pct: int,
    title: Optional[str] = None,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    """
    Helper publishing an individual field extraction event.
    """
    field_title = title or f"Field Extracted: {field_name}"
    field_msg = message or f"Extracted {field_name} = '{field_value}' with confidence {confidence_pct}%"
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.FIELD_EXTRACTED,
        title=field_title,
        message=field_msg,
        severity=Severity.INFO,
        confidence=confidence_pct,
        metadata={"field": field_name, "value": field_value, **(metadata or {})},
    )
    await event_bus.publish(event)
    return event


async def publish_mission_context_created(
    mission_id: str,
    context_data: Dict[str, Any],
    title: str = "Shared Mission Context Created",
    message: str = "Normalized adjudication context published for downstream verification nodes",
) -> Event:
    """
    Helper publishing the compiled Shared Mission Context creation event.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.MISSION_CONTEXT_CREATED,
        title=title,
        message=message,
        severity=Severity.SUCCESS,
        metadata=context_data,
    )
    await event_bus.publish(event)
    return event


async def publish_provider_lookup(
    mission_id: str,
    provider_name: Optional[str],
    gstin: Optional[str],
    resolved: bool,
    confidence: int,
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    """
    Helper publishing a provider_lookup check update.
    """
    title = f"Provider Lookup: {provider_name}" if resolved else "Provider Lookup Failed"
    message = (
        f"Resolved vendor mapping to registry entity '{provider_name}' via GSTIN: {gstin} (Confidence: {confidence}%)"
        if resolved
        else f"Registry query returned AMBIGUOUS for vendor '{provider_name}'"
    )
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.PROVIDER_LOOKUP,
        agent=AgentName.PROVIDER,
        status=AgentStatus.PENDING,
        title=title,
        message=message,
        severity=Severity.SUCCESS if resolved else Severity.WARN,
        confidence=confidence,
        metadata={"resolved": resolved, "gstin": gstin, "provider_name": provider_name, **(metadata or {})},
    )
    await event_bus.publish(event)
    return event


async def publish_provider_mcp_connected(
    mission_id: str,
    provider_name: str,
    endpoint: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    """
    Helper publishing the establishment of an MCP connection.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.PROVIDER_MCP_CONNECTED,
        agent=AgentName.PROVIDER,
        status=AgentStatus.PENDING,
        title="Provider MCP Tunnel Connected",
        message=f"Securely established live MCP session tunnel with {provider_name} registry gateway at {endpoint}",
        severity=Severity.SUCCESS,
        metadata={"provider_name": provider_name, "mcp_endpoint": endpoint, **(metadata or {})},
    )
    await event_bus.publish(event)
    return event


async def publish_provider_tool_called(
    mission_id: str,
    provider_name: str,
    tool_name: str,
    args: Dict[str, Any],
) -> Event:
    """
    Helper publishing provider tool invocation telemetry.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.PROVIDER_TOOL_CALLED,
        agent=AgentName.PROVIDER,
        status=AgentStatus.PENDING,
        title=f"Invoked Provider Tool: {tool_name}",
        message=f"Dispatched query request on tool '{tool_name}' for record validation with vendor records repository.",
        severity=Severity.INFO,
        tools_used=[tool_name],
        metadata={"provider_name": provider_name, "tool_name": tool_name, "args": args},
    )
    await event_bus.publish(event)
    return event


async def publish_provider_tool_completed(
    mission_id: str,
    provider_name: str,
    tool_name: str,
    finding: str,
    latency_ms: int,
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    """
    Helper publishing provider tool verification completed telemetry.
    """
    severity = Severity.SUCCESS if finding == "CONFIRMED" else Severity.WARN
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.PROVIDER_TOOL_COMPLETED,
        agent=AgentName.PROVIDER,
        status=AgentStatus.PENDING,
        title=f"Provider Tool Executed: {finding}",
        message=f"Tool check returned finding '{finding}' across registered digital records database.",
        severity=severity,
        latency_ms=latency_ms,
        tools_used=[tool_name],
        metadata={"provider_name": provider_name, "tool_name": tool_name, "finding": finding, **(metadata or {})},
    )
    await event_bus.publish(event)
    return event


async def publish_provider_failed(
    mission_id: str,
    provider_name: str,
    error_message: str,
    latency_ms: int,
) -> Event:
    """
    Helper publishing a provider failure event.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.PROVIDER_FAILED,
        agent=AgentName.PROVIDER,
        status=AgentStatus.ERROR,
        title="Provider Verification Anomaly",
        message=f"Execution encountered connection or schema failure: {error_message}",
        severity=Severity.ERROR,
        latency_ms=latency_ms,
        metadata={"provider_name": provider_name, "error": error_message},
    )
    await event_bus.publish(event)
    return event


async def publish_policy_loading_rules(
    mission_id: str,
    rules_source: str = "company_policy.yaml"
) -> Event:
    """
    Helper publishing policy rules loading phase.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.POLICY_LOADING_RULES,
        agent=AgentName.POLICY,
        status=AgentStatus.LOADING,
        title="Loading Corporate Reimbursement Policies",
        message=f"Reading company expense thresholds and receipt requirements from external policy file '{rules_source}'",
        severity=Severity.INFO
    )
    await event_bus.publish(event)
    return event


async def publish_policy_rule_checked(
    mission_id: str,
    rule: str,
    result: str,
    details: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Event:
    """
    Helper publishing progressive individual policy rule check metrics.
    """
    severity = Severity.SUCCESS
    status = AgentStatus.PENDING
    if result == "FLAG":
        severity = Severity.WARN
    elif result == "HARD_FAIL":
        severity = Severity.ERROR
        status = AgentStatus.ERROR

    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.POLICY_RULE_CHECKED,
        agent=AgentName.POLICY,
        status=status,
        title=f"Policy Check: {rule}",
        message=f"Rule check evaluated to [{result}]. {details}",
        severity=severity,
        metadata={"rule": rule, "result": result, "details": details, **(metadata or {})}
    )
    await event_bus.publish(event)
    return event


async def publish_policy_failed(
    mission_id: str,
    error: str,
    latency_ms: int
) -> Event:
    """
    Helper publishing a total policy parsing or engine failure event.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.POLICY_FAILED,
        agent=AgentName.POLICY,
        status=AgentStatus.ERROR,
        title="Policy Engine Failure",
        message=f"Policy evaluation was aborted due to rule format or file loading discrepancy: {error}",
        severity=Severity.ERROR,
        latency_ms=latency_ms,
        metadata={"error": error}
    )
    await event_bus.publish(event)
    return event


async def publish_pattern_history_loaded(
    mission_id: str,
    count: int
) -> Event:
    """
    Helper publishing pattern historical claims loading completion.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.PATTERN_HISTORY_LOADED,
        agent=AgentName.PATTERN,
        status=AgentStatus.LOADING,
        title="Historical Claim Records Loaded",
        message=f"Successfully fetched {count} historical claims for this member/employee",
        severity=Severity.INFO,
        metadata={"historical_claims_count": count}
    )
    await event_bus.publish(event)
    return event


async def publish_pattern_check_started(
    mission_id: str,
    detector: str
) -> Event:
    """
    Helper publishing the initiation of a specific pattern detector check.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.PATTERN_CHECK_STARTED,
        agent=AgentName.PATTERN,
        status=AgentStatus.LOADING,
        title=f"Running Pattern: {detector}",
        message=f"Evaluating claim transaction data against the '{detector}' behavioral heuristic",
        severity=Severity.INFO,
        metadata={"detector": detector}
    )
    await event_bus.publish(event)
    return event


async def publish_pattern_finding(
    mission_id: str,
    pattern_type: str,
    result: str,
    details: str,
    severity: Severity,
    metadata: Optional[Dict[str, Any]] = None
) -> Event:
    """
    Helper publishing an individual pattern detector outcome.
    """
    status = AgentStatus.SUCCESS
    if result == "FLAG":
        status = AgentStatus.WARNING
    elif result == "HARD_FAIL":
        status = AgentStatus.ERROR

    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.PATTERN_FINDING,
        agent=AgentName.PATTERN,
        status=status,
        title=f"Pattern Result: {pattern_type}",
        message=f"Check evaluated to [{result}]. {details}",
        severity=severity,
        metadata={"pattern_type": pattern_type, "result": result, "details": details, **(metadata or {})}
    )
    await event_bus.publish(event)
    return event


async def publish_pattern_summary_generated(
    mission_id: str,
    summary: str
) -> Event:
    """
    Helper publishing the generated behavioral summary.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.PATTERN_SUMMARY_GENERATED,
        agent=AgentName.PATTERN,
        status=AgentStatus.LOADING,
        title="Behavioral Summary Generated",
        message=summary,
        severity=Severity.INFO,
        metadata={"summary": summary}
    )
    await event_bus.publish(event)
    return event


async def publish_pattern_failed(
    mission_id: str,
    error: str,
    latency_ms: int
) -> Event:
    """
    Helper publishing a total pattern evaluation failure event.
    """
    event = _create_base_event(
        mission_id=mission_id,
        event_type=EventType.PATTERN_FAILED,
        agent=AgentName.PATTERN,
        status=AgentStatus.ERROR,
        title="Pattern Evaluation Failure",
        message=f"Pattern analysis was aborted due to rule engine discrepancy: {error}",
        severity=Severity.ERROR,
        latency_ms=latency_ms,
        metadata={"error": error}
    )
    await event_bus.publish(event)
    return event


