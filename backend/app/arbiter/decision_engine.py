"""
Module implementing the central Arbiter Decision Engine.
Runs deterministic rules, executes Tool Gate circuit breakers, creates escalation cases, and packages DecisionPackets.
"""

from datetime import datetime, UTC
import uuid
from typing import Dict, Any, List, Optional

from app.models.enums import EventType, AgentName, AgentStatus, Severity
from app.models.evidence import Evidence
from app.models.evidence_bundle import EvidenceBundle
from app.models.decision_packet import DecisionPacket
from app.core.event_publisher import (
    publish_agent_started,
    publish_agent_completed,
)
from app.core.event_bus import event_bus
from app.core.event_publisher import _create_base_event
from app.gates import evaluate_gate_check, execute_approval
from app.arbiter.aggregator import EvidenceAggregator
from app.arbiter.resolver import EvidenceResolver
from app.arbiter.models import Conflict
from app.core.logger import logger


class ArbiterDecisionEngine:
    """
    Central decision intelligence engine of the Nexus AI Platform.
    Evaluates evidence bundles, runs topological conflict resolutions, and dispatches guardrail gates.
    """

    @classmethod
    async def evaluate_bundle(cls, bundle: EvidenceBundle) -> DecisionPacket:
        """
        Runs the complete centralized arbitration pipeline over the given EvidenceBundle.
        
        Args:
            bundle: Consumed EvidenceBundle containing parallel agent findings.
            
        Returns:
            DecisionPacket: Pristine adjudication container delivered to the frontend.
        """
        mission_id = bundle.mission_id
        start_time = datetime.now(UTC)
        logger.info(f"[ARBITER ENGINE] Commencing adjudication pipeline for mission_id={mission_id}")

        # 1. Publish: arbiter_started
        start_event = _create_base_event(
            mission_id=mission_id,
            event_type=EventType.ARBITER_STARTED,
            agent=AgentName.ARBITER,
            status=AgentStatus.LOADING,
            title="Arbiter Decision Engine Activated",
            message="Evaluating consolidated evidence logs to formulate deterministic recommendation",
            severity=Severity.INFO
        )
        await event_bus.publish(start_event)

        # 2. Publish: evidence_aggregation_started
        agg_started_event = _create_base_event(
            mission_id=mission_id,
            event_type=EventType.EVIDENCE_AGGREGATION_STARTED,
            agent=AgentName.ARBITER,
            status=AgentStatus.LOADING,
            title="Evidence Aggregation Initiated",
            message="Scanning specialist results and validating receipt signatures for completeness",
            severity=Severity.INFO
        )
        await event_bus.publish(agg_started_event)

        # Execute Aggregator
        agg_report = EvidenceAggregator.aggregate(bundle)
        findings = agg_report["findings"]
        missing_specialists = agg_report["missing_specialists"]

        # Check for total incomplete failure: No evidence whatsoever
        if not findings and len(missing_specialists) == 3:
            logger.error(f"[ARBITER ENGINE] Critical Error: Adjudication bundle is empty for mission_id={mission_id}")
            err_packet = DecisionPacket(
                mission=mission_id,
                recommendation="ESCALATE",
                reason="Incomplete claims evidence: Critical Provider, Policy, and Pattern findings are completely missing.",
                confidence=0,
                conflicts=[],
                human_question="CRITICAL FAILURE: No specialist validation evidence was loaded. Would you like to force-escalate for manual audit?",
                timeline=[{"checkpoint": "ARBITER_ERROR", "message": "Missing all specialist findings"}],
                audit_summary={
                    "timestamp": datetime.now(UTC).isoformat(),
                    "status": "ERROR",
                    "error": "No specialist data loaded"
                }
            )
            # Publish completion failure telemetry
            end_event = _create_base_event(
                mission_id=mission_id,
                event_type=EventType.DECISION_COMPLETED,
                agent=AgentName.ARBITER,
                status=AgentStatus.ERROR,
                title="Arbitration Blocked",
                message="Aggregation failed. Specialist findings are completely missing.",
                severity=Severity.ERROR
            )
            await event_bus.publish(end_event)
            return err_packet

        # 3. Detect Conflicts
        conflicts = EvidenceResolver.detect_conflicts(findings)
        
        # Publish if conflicts found
        if conflicts:
            conflict_event = _create_base_event(
                mission_id=mission_id,
                event_type=EventType.CONFLICT_DETECTED,
                agent=AgentName.ARBITER,
                status=AgentStatus.WARNING,
                title="Logical Conflicts Identified",
                message=f"Detected {len(conflicts)} direct logical disagreements between specialist outputs.",
                severity=Severity.WARN,
                metadata={"conflicts": [c.model_dump() for c in conflicts]}
            )
            await event_bus.publish(conflict_event)

        # 4. Perform Resolution Round (if conflicts exist)
        resolution_summary = "All specialist checks align with standard company guidelines."
        recalculated_confidence = 100
        recommended_action = "PROCEED_TO_STANDARD_PROTOCOL"
        
        if conflicts:
            res_started_event = _create_base_event(
                mission_id=mission_id,
                event_type=EventType.RESOLUTION_ROUND_STARTED,
                agent=AgentName.ARBITER,
                status=AgentStatus.LOADING,
                title="Conflict Resolution Round Active",
                message="Restating opposing findings and applying reliability weights to balance claims",
                severity=Severity.INFO
            )
            await event_bus.publish(res_started_event)

            # Resolve conflict
            resolution = EvidenceResolver.resolve(findings, conflicts)
            recalculated_confidence = resolution.recalculated_confidence
            resolution_summary = resolution.resolution_summary
            recommended_action = resolution.recommended_action

            res_completed_event = _create_base_event(
                mission_id=mission_id,
                event_type=EventType.RESOLUTION_COMPLETED,
                agent=AgentName.ARBITER,
                status=AgentStatus.SUCCESS,
                title="Discrepancy Round Completed",
                message="Logical consensus reached. Formulating deterministic recommendation.",
                severity=Severity.SUCCESS,
                metadata=resolution.model_dump()
            )
            await event_bus.publish(res_completed_event)
        else:
            # Standard confidence calculation with zero conflicts
            resolution = EvidenceResolver.resolve(findings, [])
            recalculated_confidence = resolution.recalculated_confidence

        # 5. Apply Deterministic Rules (Decision Protocol)
        has_error = any(f.severity == Severity.ERROR for f in findings)
        has_warn = any(f.severity == Severity.WARN for f in findings)

        if recommended_action == "FORCE_REJECT":
            recommendation = "REJECT"
            reason = (
                "Claim rejected due to critical compliance or fraud flags identified. "
                "Behavioral risk detectors or strict policy audits found severe anomalies override verified ledgers."
            )
        elif recommended_action == "FORCE_ESCALATE":
            recommendation = "ESCALATE"
            reason = (
                "Claim escalated for review. Mild compliance threshold flags or behavioral anomalies "
                "require human oversight."
            )
        elif has_error:
            recommendation = "REJECT"
            reason = "Claim rejected. Severe compliance violations or unregistered billing anomalies detected."
        elif has_warn:
            recommendation = "ESCALATE"
            reason = "Claim escalated. Verification warnings or spend limit warning thresholds were triggered."
        else:
            recommendation = "APPROVE"
            reason = "Claim approved. Specialist checks verified provider ledgers, limits, and historical patterns without anomalies."

        # Handle incomplete runs as manual escalation
        if missing_specialists:
            reason += f" Warning: Specialist output is missing for {', '.join(missing_specialists)}."
            if recommendation == "APPROVE":
                recommendation = "ESCALATE"

        # 6. Tool Gate Integration (Evaluate execute_approval circuit-breaker)
        gate_event = _create_base_event(
            mission_id=mission_id,
            event_type=EventType.GATE_CHECK,
            agent=AgentName.ARBITER,
            status=AgentStatus.LOADING,
            title="Tool Gate Boundary Check",
            message="Invoking evaluate_gate_check circuit breaker from gates.py",
            severity=Severity.INFO
        )
        await event_bus.publish(gate_event)
        
        gate_cleared = evaluate_gate_check(EventType.GATE_CHECK.value, {"recommendation": recommendation})
        if not gate_cleared:
            logger.warning(f"[ARBITER ENGINE] Tool Gate circuit-breaker halted execution for mission_id={mission_id}")
            recommendation = "ESCALATE"
            reason = "Gate Halted: Tool Gate security boundaries intercepted the automated outcome and triggered a manual audit."
        elif recommendation == "APPROVE":
            # Invoke physical tool gate approval executor
            approval_cleared = execute_approval(mission_id, {"recommendation": recommendation})
            if not approval_cleared:
                logger.warning(f"[ARBITER ENGINE] execute_approval() rejected action for mission_id={mission_id}")
                recommendation = "ESCALATE"
                reason = "Gate Halted: The execute_approval Tool Gate halted execution due to gateway security limits."

        # 7. Generate Escalation Case (if ESCALATE)
        human_question = None
        if recommendation == "ESCALATE":
            human_question = cls._generate_human_question(findings, conflicts, missing_specialists)

        # 8. Publish: decision_recommended
        rec_event = _create_base_event(
            mission_id=mission_id,
            event_type=EventType.DECISION_RECOMMENDED,
            agent=AgentName.ARBITER,
            status=AgentStatus.SUCCESS,
            title="Decision Recommended",
            message=f"Recommended State: [{recommendation}]. Reasoning: {reason}",
            severity=Severity.SUCCESS if recommendation == "APPROVE" else (Severity.WARN if recommendation == "ESCALATE" else Severity.ERROR),
            confidence=recalculated_confidence,
            metadata={"recommendation": recommendation, "reason": reason}
        )
        await event_bus.publish(rec_event)

        # Assemble the Decision Packet timeline checks
        timeline = []
        for f in findings:
            timeline.append({
                "agent": f.agent.value,
                "title": f.title,
                "status": "cleared" if f.severity == Severity.SUCCESS else ("warning" if f.severity == Severity.WARN else "failed"),
                "message": f.description,
                "timestamp": f.timestamp.isoformat()
            })

        elapsed_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

        # 9. Pack and Return DecisionPacket
        packet = DecisionPacket(
            mission=mission_id,
            recommendation=recommendation,
            reason=reason,
            confidence=recalculated_confidence,
            provider_evidence=bundle.provider_findings,
            policy_evidence=bundle.policy_findings,
            pattern_evidence=bundle.pattern_findings,
            conflicts=[c.model_dump() for c in conflicts],
            resolution_summary=resolution_summary,
            human_question=human_question,
            timeline=timeline,
            audit_summary={
                "adjudication_timestamp": datetime.now(UTC).isoformat(),
                "latency_ms": elapsed_ms,
                "is_complete": len(missing_specialists) == 0,
                "missing_specialists": missing_specialists,
                "gate_circuit_breaker_cleared": gate_cleared,
                "conflict_count": len(conflicts),
                "weighted_resolution_summary": resolution_summary
            }
        )

        # 10. Publish: decision_completed (Decision / Arbiter complete event)
        end_event = _create_base_event(
            mission_id=mission_id,
            event_type=EventType.DECISION_COMPLETED,
            agent=AgentName.ARBITER,
            status=AgentStatus.SUCCESS,
            title="Adjudication final decision loaded",
            message="Decision Packet finalized and successfully locked in Mission Database",
            severity=Severity.SUCCESS if recommendation == "APPROVE" else (Severity.WARN if recommendation == "ESCALATE" else Severity.ERROR),
            confidence=recalculated_confidence,
            metadata={"decision_packet": packet.model_dump()}
        )
        await event_bus.publish(end_event)

        return packet

    @classmethod
    def _generate_human_question(cls, findings: List[Evidence], conflicts: List[Conflict], missing_specialists: List[str]) -> str:
        """
        Generates premium review questions and case summaries to assist human audit teams.
        """
        bullet_points = []
        
        # 1. Summarize missing files
        if missing_specialists:
            bullet_points.append(f"- Missing specialist analysis data for: {', '.join(missing_specialists)}")

        # 2. Extract warnings/errors from active evidence
        for f in findings:
            if f.severity in [Severity.WARN, Severity.ERROR]:
                bullet_points.append(f"- {f.agent.value} Flag: {f.title} ({f.description})")

        # 3. Add conflict outlines
        for c in conflicts:
            bullet_points.append(f"- Discrepancy Conflict: {c.description}")

        case_summary = "\n".join(bullet_points)
        
        question = (
            f"### 📋 Case Review Summary\n"
            f"This claim was flagged for manual human verification due to compliance anomalies or data limitations.\n\n"
            f"**Evidence Alerts Detected:**\n"
            f"{case_summary}\n\n"
            f"**Human Verification Query:**\n"
            f"Do you wish to bypass these warnings and force-approve this claim based on manual receipt matching, "
            f"or would you like to reject this claim for compliance violations?"
        )
        return question
