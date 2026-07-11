"""
Unit and integration test suite verifying the Gemma Intelligence Service.
Tests structured summary generation, consistency checks, timeout fallback rules,
and FastAPI web endpoint routing stability.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.mission_manager import mission_manager
from app.core.event_bus import event_bus
from app.models.enums import EventType
from app.gemma.service import GemmaIntelligenceService, gemma_tracker
from app.gemma.models import GemmaExplanationPacket

client = TestClient(app)


@pytest.mark.anyio
async def test_gemma_pipeline_success_approved():
    """
    Verifies that compiling a Gemma explanation packet succeeds for an APPROVED claim when API is mocked.
    Ensures that correct fields are generated, cached, and proper events are dispatched.
    """
    mission_id = "RUN-GEMMA-001"
    claim_id = "NEX-GEMMA-001"
    
    # 1. Setup in-memory mock mission and store mock decision packet
    await mission_manager.create_mission(mission_id=mission_id, claim_id=claim_id)
    decision_packet = {
        "claim_id": claim_id,
        "recommendation": "APPROVE",
        "reason": "GSTIN registration is valid and clinical limits are in bounds.",
        "confidence": 98,
        "provider_evidence": {"description": "Active registration verified.", "status": "success", "severity": "INFO"},
        "policy_evidence": {"description": "Claim is within allowable individual limits.", "status": "success", "severity": "INFO"},
        "pattern_evidence": {"description": "No historical behavior flags found.", "status": "success", "severity": "INFO"}
    }
    await mission_manager.attach_metadata(mission_id, {"decision_packet": decision_packet})

    # Subscribe to EventBus to verify dispatched events
    event_queue = await event_bus.subscribe(mission_id)

    # 2. Mock google-genai Client response
    mock_genai_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = """
    {
        "behavior_summary": "No unusual patterns or claim anomalies detected across provider or pattern historical registries.",
        "decision_explanation": "Adjudication approved claim NEX-GEMMA-001 as all participating specialists (Provider, Policy, and Pattern) cleared verification checks without flags.",
        "executive_summary": "Claim NEX-GEMMA-001 approved successfully with zero compliance or fraud flags.",
        "finance_summary": "Claim NEX-GEMMA-001 approved. All item costs are within standard guidelines.",
        "employee_summary": "Your claim has been approved. Reimbursement processing has been initiated.",
        "review_status": "MATCH",
        "review_explanation": "Decision is fully consistent as all specialist validation records were successful."
    }
    """
    mock_genai_client.models.generate_content.return_value = mock_response

    # Ensure settings key is present to bypass empty key early-exit in client
    with patch.object(settings, "GEMINI_API_KEY", "MOCK_KEY"), \
         patch("google.genai.Client", return_value=mock_genai_client):
        
        # 3. Trigger explanation compilation
        packet = await GemmaIntelligenceService.get_or_create_explanation(mission_id)

        # 4. Assert Pydantic validation and field values
        assert isinstance(packet, GemmaExplanationPacket)
        assert packet.mission_id == mission_id
        assert "Active registration verified" not in packet.behavior_summary  # ensures it is not hardcoded fallback
        assert "No unusual patterns" in packet.behavior_summary
        assert packet.decision_review == "MATCH: Decision is fully consistent as all specialist validation records were successful."
        assert packet.metadata["gemma_source"] == "gemma_api_studio"

        # 5. Verify caching of compiled packet inside mission metadata
        mission = await mission_manager.get_mission(mission_id)
        assert "gemma_explanation_packet" in mission.metadata
        assert mission.metadata["gemma_explanation_packet"]["behavior_summary"] == packet.behavior_summary

        # 6. Verify that all expected event checkpoints were published to EventBus
        received_types = []
        while not event_queue.empty():
            ev = await event_queue.get()
            received_types.append(ev.event_type)
            event_queue.task_done()

        assert EventType.GEMMA_STARTED in received_types
        assert EventType.GEMMA_SUMMARY_GENERATED in received_types
        assert EventType.GEMMA_REVIEW_COMPLETED in received_types
        assert EventType.GEMMA_COMPLETED in received_types


@pytest.mark.anyio
async def test_gemma_pipeline_graceful_degradation_on_timeout():
    """
    Verifies that Gemma service degrades gracefully to procedural fallback when Gemma Client triggers a timeout.
    Asserts that the backend continues and returns standard fallback packet with behavior_summary = None.
    """
    mission_id = "RUN-GEMMA-TIMEOUT"
    claim_id = "NEX-GEMMA-TIMEOUT"
    
    await mission_manager.create_mission(mission_id=mission_id, claim_id=claim_id)
    decision_packet = {
        "claim_id": claim_id,
        "recommendation": "APPROVE",
        "reason": "Clean records.",
        "confidence": 95,
        "provider_evidence": {"description": "Active provider.", "status": "success", "severity": "INFO"},
        "policy_evidence": {"description": "Limits ok.", "status": "success", "severity": "INFO"},
        "pattern_evidence": {"description": "No patterns found.", "status": "success", "severity": "INFO"}
    }
    await mission_manager.attach_metadata(mission_id, {"decision_packet": decision_packet})

    event_queue = await event_bus.subscribe(mission_id)

    # Mock timeout by raising asyncio.TimeoutError when generate_explanation is called
    with patch.object(settings, "GEMINI_API_KEY", "MOCK_KEY"), \
         patch("app.gemma.client.GemmaClient.generate_explanation", side_effect=asyncio.TimeoutError()):
        
        packet = await GemmaIntelligenceService.get_or_create_explanation(mission_id)

        # Assert fallback format
        assert isinstance(packet, GemmaExplanationPacket)
        assert packet.behavior_summary is None  # null as requested
        assert "MATCH" in packet.decision_review
        assert packet.metadata["gemma_source"] == "fallback_procedural"

        # Verify cached packet in mission
        mission = await mission_manager.get_mission(mission_id)
        assert mission.metadata["gemma_explanation_packet"]["behavior_summary"] is None

        # Verify gemma_failed event dispatched
        received_types = []
        while not event_queue.empty():
            ev = await event_queue.get()
            received_types.append(ev.event_type)
            event_queue.task_done()

        assert EventType.GEMMA_STARTED in received_types
        assert EventType.GEMMA_FAILED in received_types


@pytest.mark.anyio
async def test_gemma_pipeline_parsing_error_fallback():
    """
    Verifies that the Gemma service falls back gracefully when the Gemma client returns bad/invalid JSON structure.
    """
    mission_id = "RUN-GEMMA-BADJSON"
    claim_id = "NEX-GEMMA-BADJSON"
    
    await mission_manager.create_mission(mission_id=mission_id, claim_id=claim_id)
    decision_packet = {
        "claim_id": claim_id,
        "recommendation": "REJECT",
        "reason": "Duplicate claim detected by Pattern Agent.",
        "confidence": 99,
        "provider_evidence": {"description": "Active provider.", "status": "success", "severity": "INFO"},
        "policy_evidence": {"description": "Limits ok.", "status": "success", "severity": "INFO"},
        "pattern_evidence": {"description": "Duplicate claim NEX-002 submitted yesterday.", "status": "error", "severity": "ERROR"}
    }
    await mission_manager.attach_metadata(mission_id, {"decision_packet": decision_packet})

    # Return garbage string instead of Pydantic JSON string
    mock_genai_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "INVALID_GARBAGE_STRING_NOT_JSON"
    mock_genai_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "GEMINI_API_KEY", "MOCK_KEY"), \
         patch("google.genai.Client", return_value=mock_genai_client):
        
        packet = await GemmaIntelligenceService.get_or_create_explanation(mission_id)

        # Assert fallback format
        assert isinstance(packet, GemmaExplanationPacket)
        assert packet.behavior_summary is None
        assert "MATCH" in packet.decision_review
        assert "compliance/fraud validation failures" in packet.decision_review
        assert packet.metadata["gemma_source"] == "fallback_procedural"


def test_get_explanation_endpoint_success():
    """
    Verifies FastAPI routing integration for retrieving Gemma explanations.
    """
    mission_id = "RUN-GEMMA-API"
    claim_id = "NEX-GEMMA-API"
    
    # Pre-populate cached packet inside active mission records
    async def setup_mission():
        await mission_manager.create_mission(mission_id=mission_id, claim_id=claim_id)
        cached_packet = GemmaExplanationPacket(
            mission_id=mission_id,
            behavior_summary="Anomalous behavior summary.",
            decision_explanation="Because of specialist checks.",
            executive_summary="Executive summary brief.",
            finance_summary="Finance summary brief.",
            employee_summary="Employee summary brief.",
            decision_review="MATCH: Audited successfully.",
            generated_at="2026-07-11T12:00:00Z",
            metadata={"gemma_source": "cached_test"}
        )
        await mission_manager.attach_metadata(mission_id, {"gemma_explanation_packet": cached_packet.model_dump()})

    asyncio.run(setup_mission())

    # Dispatch web GET request
    response = client.get(f"/claims/{mission_id}/explanation")
    
    assert response.status_code == 200
    data = response.json()
    assert data["mission_id"] == mission_id
    assert data["behavior_summary"] == "Anomalous behavior summary."
    assert data["decision_review"] == "MATCH: Audited successfully."


def test_get_explanation_endpoint_not_found():
    """
    Verifies that calling the explanation endpoint with an invalid mission ID returns 404.
    """
    response = client.get("/claims/INVALID-MISSION-9999/explanation")
    assert response.status_code == 404
