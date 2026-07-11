"""
Module implementing the central Gemma Intelligence Service coordinator.
Orchestrates prompt assembly, client invocations, response validation,
real-time SSE log publishing, and thread-safe diagnostic stats tracking.
"""

import asyncio
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.logger import logger
from app.core.mission_manager import mission_manager
from app.core.event_bus import event_bus
from app.models.enums import EventType, Severity, AgentStatus
from app.models.event import Event
from app.gemma.models import GemmaExplanationPacket, GemmaGenerationTarget
from app.gemma.client import GemmaClient
from app.gemma.summarizer import build_summaries_context, enforce_summary_word_limits
from app.gemma.reviewer import build_reviewer_context, run_procedural_consistency_check


class GemmaHealthTracker:
    """Thread-safe statistics tracker managing health metrics for the Gemma Intelligence Service."""
    def __init__(self) -> None:
        self.status = "healthy"
        self.model_name = settings.GEMMA_MODEL or "gemma2-27b-it"
        self.latency_ms = 0
        self.last_successful_call: Optional[str] = None
        self._lock = asyncio.Lock()

    async def update_success(self, latency_ms: int) -> None:
        async with self._lock:
            self.status = "healthy"
            self.latency_ms = latency_ms
            self.last_successful_call = datetime.now(timezone.utc).isoformat()

    async def update_failure(self) -> None:
        async with self._lock:
            self.status = "degraded"

    async def get_metrics(self) -> Dict[str, Any]:
        async with self._lock:
            return {
                "status": self.status,
                "model_name": self.model_name,
                "latency_ms": self.latency_ms,
                "last_successful_call": self.last_successful_call
            }


# Global health tracker singleton
gemma_tracker = GemmaHealthTracker()


class GemmaIntelligenceService:
    """
    Central service coordinating explainability audits and persona-targeted summary generations
    utilizing Gemma models on Google AI Studio.
    """

    @staticmethod
    def _create_gemma_event(
        mission_id: str,
        event_type: EventType,
        title: str,
        message: str,
        severity: Severity = Severity.INFO,
        status: AgentStatus = AgentStatus.LOADING,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Event:
        """Helper to create standard platform-conforming SSE Event records."""
        return Event(
            event_id=str(uuid.uuid4()),
            mission_id=mission_id,
            event_type=event_type,
            agent=None,  # Gemma is an intelligence layer, not an autonomous planning agent
            status=status,
            title=title,
            message=message,
            severity=severity,
            confidence=100,
            latency_ms=0,
            tools_used=[],
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {}
        )

    @classmethod
    def _compile_procedural_fallback_packet(
        cls,
        mission_id: str,
        claim_id: str,
        decision_packet: Dict[str, Any]
    ) -> GemmaExplanationPacket:
        """Compiles a safe, zero-dependency local fallback packet under API errors or offline status."""
        logger.info(f"[GEMMA SERVICE] Compiling procedural fallback packet for mission={mission_id}")

        # Compute procedural review consistency checks
        review_status, review_reason = run_procedural_consistency_check(decision_packet)

        reason = decision_packet.get("reason", "Manual adjudication override initiated.")
        rec = decision_packet.get("recommendation", "ESCALATE")

        return GemmaExplanationPacket(
            mission_id=mission_id,
            behavior_summary=None,  # Null under failures as requested
            decision_explanation=(
                f"Procedural Analysis: Claim {claim_id} was adjudicated with outcome {rec}. "
                f"Primary decision trigger: {reason}."
            ),
            executive_summary=f"Corporate overview of claim {claim_id} showing outcome {rec}.",
            finance_summary=f"Cost audit summary of claim {claim_id} with status {rec}.",
            employee_summary=f"Adjudication notification for claim {claim_id}. Status: {rec}.",
            decision_review=f"{review_status}: {review_reason}",
            generated_at=datetime.now(timezone.utc).isoformat(),
            metadata={"gemma_source": "fallback_procedural"}
        )

    @classmethod
    async def get_or_create_explanation(cls, mission_id: str) -> GemmaExplanationPacket:
        """
        Retrieves an existing cached Gemma explanation, or triggers a fresh generation pipeline.

        Args:
            mission_id: The unique alphanumeric active run ID.

        Returns:
            GemmaExplanationPacket: Validated explanation packet. Never fails the mission.
        """
        mission = await mission_manager.get_mission(mission_id)
        if not mission:
            logger.error(f"[GEMMA SERVICE] Mission {mission_id} not found.")
            raise ValueError(f"Mission {mission_id} does not exist.")

        claim_id = mission.claim_id

        # 1. Return cached explanation packet if already generated
        cached_data = mission.metadata.get("gemma_explanation_packet")
        if cached_data:
            logger.info(f"[GEMMA SERVICE] Returning cached Gemma explanation for mission={mission_id}")
            return GemmaExplanationPacket.model_validate(cached_data)

        logger.info(f"[GEMMA SERVICE] Triggering fresh Gemma analysis pipeline for mission={mission_id}")

        # Extract Arbiter decision details
        decision_packet = mission.metadata.get("decision_packet")
        if not decision_packet:
            logger.info(f"[GEMMA SERVICE] Decision packet missing for mission={mission_id}. Reconstructing default.")
            decision_packet = {
                "claim_id": claim_id,
                "recommendation": "ESCALATE",
                "reason": "Flagged for manual policy override checks.",
                "confidence": 85,
                "provider_evidence": {"description": "Provider verified active", "status": "success"},
                "policy_evidence": {"description": "Policy check warnings flagged", "status": "warning"},
                "pattern_evidence": {"description": "No fraud indicators found", "status": "success"}
            }

        # Publish Event: gemma_started
        await event_bus.publish(
            cls._create_gemma_event(    
                mission_id=mission_id,
                event_type=EventType.GEMMA_STARTED,
                title="Gemma Analysis Started",
                message=f"Initializing independent explainability layer utilizing model={settings.GEMMA_MODEL or 'gemma2-27b-it'}."
            )
        )

        start_time = time.perf_counter()

        # 2. Build detailed prompts combining summaries and review context
        summaries_context = build_summaries_context(decision_packet, mission.metadata)
        reviewer_context = build_reviewer_context(decision_packet)

        system_instruction = (
            "You are the Senior Explainability and Trust Service powered by Google Gemma.\n"
            "Your sole task is to analyze claims adjudication results and output structured details in JSON.\n"
            "\n"
            "CRITICAL BEHAVIOR BOUNDARIES:\n"
            "- You never make approval decisions. You only explain decisions made by the Arbiter.\n"
            "- You never perform invoice, rule, or fraud validations.\n"
            "- You must strictly adhere to the provided facts and never invent facts.\n"
            "- Output JSON adhering exactly to the provided response schema."
        )

        prompt = (
            "Analyze these claim findings and Arbiter decisions to generate an explanation package:\n\n"
            f"{summaries_context}\n\n"
            f"{reviewer_context}\n\n"
            "Please populate all fields of the response schema, strictly adhering to word limits:\n"
            "- behavior_summary: Max 80 words.\n"
            "- executive_summary: Max 60 words.\n"
            "- finance_summary: Max 60 words.\n"
            "- employee_summary: Max 60 words.\n"
            "- review_status: MATCH or REVIEW.\n"
            "- review_explanation: Max 50 words."
        )

        # 3. Call Gemma SDK Client
        client = GemmaClient()
        target: Optional[GemmaGenerationTarget] = None

        try:
            target = await client.generate_explanation(prompt, system_instruction)
        except Exception as err:
            logger.error(f"[GEMMA SERVICE] Gemma generation crashed: {err}", exc_info=True)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # 4. Handle results or fall back gracefully
        if target:
            # Update health metrics
            await gemma_tracker.update_success(latency_ms)

            # Enforce limits (extra guardrails)
            summaries = enforce_summary_word_limits(
                target.behavior_summary,
                target.executive_summary,
                target.finance_summary,
                target.employee_summary
            )

            # Publish Event: gemma_summary_generated
            await event_bus.publish(
                cls._create_gemma_event(
                    mission_id=mission_id,
                    event_type=EventType.GEMMA_SUMMARY_GENERATED,
                    title="Gemma Summaries Compiled",
                    message="Multi-persona targeted summaries and behavioral indicators generated successfully."
                )
            )

            # Publish Event: gemma_review_completed
            await event_bus.publish(
                cls._create_gemma_event(
                    mission_id=mission_id,
                    event_type=EventType.GEMMA_REVIEW_COMPLETED,
                    title="Decision Review Completed",
                    message=f"Logical consistency review completed. Outcome status: {target.review_status}"
                )
            )

            # Assemble GemmaExplanationPacket
            packet = GemmaExplanationPacket(
                mission_id=mission_id,
                behavior_summary=summaries["behavior_summary"],
                decision_explanation=target.decision_explanation,
                executive_summary=summaries["executive_summary"],
                finance_summary=summaries["finance_summary"],
                employee_summary=summaries["employee_summary"],
                decision_review=f"{target.review_status}: {target.review_explanation}",
                generated_at=datetime.now(timezone.utc).isoformat(),
                metadata={
                    "gemma_model": client.model_name,
                    "latency_ms": latency_ms,
                    "gemma_source": "gemma_api_studio"
                }
            )

            # Cache the packet
            await mission_manager.attach_metadata(mission_id, {"gemma_explanation_packet": packet.model_dump()})

            # Publish Event: gemma_completed
            await event_bus.publish(
                cls._create_gemma_event(
                    mission_id=mission_id,
                    event_type=EventType.GEMMA_COMPLETED,
                    title="Gemma Trust Analysis Complete",
                    message="Explainability package compiled and attached to mission audit trail successfully.",
                    severity=Severity.SUCCESS,
                    status=AgentStatus.SUCCESS,
                    metadata={"explanation_packet": packet.model_dump()}
                )
            )

            return packet

        else:
            # Degrade diagnostics status
            await gemma_tracker.update_failure()

            # Compile fallback packet
            packet = cls._compile_procedural_fallback_packet(mission_id, claim_id, decision_packet)

            # Cache the fallback too to prevent repeated API hitting
            await mission_manager.attach_metadata(mission_id, {"gemma_explanation_packet": packet.model_dump()})

            # Publish Event: gemma_failed
            await event_bus.publish(
                cls._create_gemma_event(
                    mission_id=mission_id,
                    event_type=EventType.GEMMA_FAILED,
                    title="Gemma Intelligence Bypassed",
                    message="API limits, timeouts, or credentials missing. Bypassing Gemma analysis and continuing.",
                    severity=Severity.WARN,
                    status=AgentStatus.WARNING
                )
            )

            return packet
