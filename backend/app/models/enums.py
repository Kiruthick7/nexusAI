"""
Module declaring shared system enumerations for the Nexus AI Operations Platform.

These enums act as the type boundaries for state machines, events, and log severity levels
communicated between backend components and frontend consumers.
"""

from enum import Enum


class EventType(str, Enum):
    """
    Canonical system event names mapping processing checkpoints.
    """
    WORKFLOW_STARTED = "workflow_started"
    INTAKE_STARTED = "intake_started"
    EXTRACTION_COMPLETED = "extraction_completed"
    PLANNER_STARTED = "planner_started"
    PLANNER_DISPATCH = "planner_dispatch"
    PROVIDER_STARTED = "provider_started"
    PROVIDER_COMPLETED = "provider_completed"
    POLICY_STARTED = "policy_started"
    POLICY_COMPLETED = "policy_completed"
    PATTERN_STARTED = "pattern_started"
    PATTERN_COMPLETED = "pattern_completed"
    CONFLICT_DETECTED = "conflict_detected"
    ARBITER_STARTED = "arbiter_started"
    ARBITER_COMPLETED = "arbiter_completed"
    GATE_CHECK = "gate_check"
    HUMAN_REQUIRED = "human_required"
    DECISION = "decision"
    WORKFLOW_COMPLETED = "workflow_completed"


class AgentName(str, Enum):
    """
    Enumerated boundaries for executing AI Agents.
    """
    PLANNER = "PlannerAgent"
    PROVIDER = "ProviderAgent"
    POLICY = "PolicyAgent"
    PATTERN = "PatternAgent"
    ARBITER = "ArbiterAgent"


class Severity(str, Enum):
    """
    Visual severity status indicators for dashboard rendering overlays.
    """
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARN = "WARN"
    ERROR = "ERROR"


class WorkflowStatus(str, Enum):
    """
    High-level state-machine workflow phase tracking indices.
    """
    IDLE = "IDLE"
    INGESTING = "INGESTING"
    PLANNING = "PLANNING"
    ANALYZING = "ANALYZING"
    ARBITRATING = "ARBITRATING"
    COMPLETED = "COMPLETED"


class AgentStatus(str, Enum):
    """
    Agent sub-status indicators tracked during parallel evaluations.
    """
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    WARNING = "warning"
    PENDING = "pending"
    ERROR = "error"
