"""
Unit and integration test suite verifying the Human Escalation Service.
Tests structured summary generation, TTS synthesis fallback rules, GCS mock fallbacks,
and FastAPI web endpoint routing stability.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.mission_manager import mission_manager
from app.core.event_bus import event_bus
from app.models.enums import EventType, WorkflowStatus
from app.escalation.service import HumanEscalationService, escalation_tracker
from app.escalation.models import EscalationPacket

client = TestClient(app)


@pytest.mark.anyio
async def test_full_escalation_pipeline_success():
    """
    Verifies that compiling a fresh escalation package succeeds when API dependencies are mocked.
    Ensures that correct fields are generated, cached, and all 7 required events are dispatched.
    """
    mission_id = "RUN-TEST-001"
    claim_id = "NEX-TEST-001"
    
    # 1. Setup in-memory mock mission and store mock decision packet
    await mission_manager.create_mission(mission_id=mission_id, claim_id=claim_id)
    decision_packet = {
        "mission": mission_id,
        "recommendation": "ESCALATE",
        "reason": "Split-billing anomaly detected by Pattern Agent: Two dental claims under $500 submitted within 2 hours.",
        "confidence": 92,
        "provider_evidence": {"description": "Precision Dental active registration verified."},
        "policy_evidence": {"description": "Claim is within individual limit, but flagged by behavioral pattern."},
        "pattern_evidence": {
            "description": "FLAGGED: Transaction frequency alert.",
            "metadata": {"gemma_summary": "Suspicious transaction clustering detected."}
        },
        "audit_summary": {"timestamp": "2026-07-11T12:00:00Z", "latency_ms": 1500}
    }
    await mission_manager.attach_metadata(mission_id, {"decision_packet": decision_packet})

    # Subscribe to EventBus to verify dispatched events
    event_queue = await event_bus.subscribe(mission_id)

    # 2. Mock GenAI Client for structured outputs and TTS synthesis
    mock_genai_client = MagicMock()
    
    # Mock LLM structured analysis output
    mock_response_llm = MagicMock()
    mock_response_llm.text = '{"summary": "The claim of dental treatment from Precision Dental has been flagged as suspicious due to a split-billing transaction clustering anomaly where multiple claims under $500 were submitted within a short timeframe.", "human_question": "Can you verify if these two dentist visits were for separate clinical procedures?"}'
    
    # Mock TTS audio output candidate
    mock_response_tts = MagicMock()
    mock_part = MagicMock()
    mock_part.inline_data.data = b"MOCK_WAV_AUDIO_DATA_FOR_BRIEFING"
    mock_response_tts.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]

    # Side effect returning LLM summary first, then TTS audio
    mock_genai_client.models.generate_content.side_effect = [
        mock_response_llm,
        mock_response_tts
    ]

    with patch.object(settings, "GEMINI_API_KEY", "MOCK_KEY"), \
         patch("google.genai.Client", return_value=mock_genai_client), \
         patch("app.escalation.storage.upload_escalation_audio", return_value="http://localhost:8000/public/audio/RUN-TEST-001.wav"):
        
        # 3. Trigger package compilation
        packet = await HumanEscalationService.get_or_create_package(mission_id)

        # 4. Assert Pydantic validation and field values
        assert isinstance(packet, EscalationPacket)
        assert packet.mission_id == mission_id
        assert packet.claim_id == claim_id
        assert "split-billing transaction clustering anomaly" in packet.summary
        assert packet.human_question == "Can you verify if these two dentist visits were for separate clinical procedures?"
        assert packet.audio_url == "http://localhost:8000/public/audio/RUN-TEST-001.wav"
        assert packet.audio_duration > 0.0
        assert packet.confidence == 92

        # 5. Verify caching of compiled packet inside mission metadata
        mission = await mission_manager.get_mission(mission_id)
        assert "escalation_packet" in mission.metadata
        assert mission.metadata["escalation_packet"]["audio_url"] == "http://localhost:8000/public/audio/RUN-TEST-001.wav"

        # 6. Verify that all 7 event checkpoints were published to EventBus
        received_types = []
        while not event_queue.empty():
            ev = await event_queue.get()
            received_types.append(ev.event_type)
            event_queue.task_done()

        expected_checkpoints = [
            EventType.ESCALATION_STARTED,
            EventType.SUMMARY_GENERATED,
            EventType.HUMAN_QUESTION_GENERATED,
            EventType.TTS_STARTED,
            EventType.TTS_COMPLETED,
            EventType.AUDIO_UPLOADED,
            EventType.ESCALATION_COMPLETED
        ]
        
        for checkpoint in expected_checkpoints:
            assert checkpoint in received_types

    # Cleanup subscriber to avoid leaks
    await event_bus.unsubscribe(mission_id, event_queue)
    await mission_manager.clear_mission(mission_id)


@pytest.mark.anyio
async def test_escalation_graceful_tts_degradation():
    """
    Verifies that if Text-to-Speech synthesis raises an API exception, the service
    gracefully recovers, sets audio_url = None, and compiles the rest of the package successfully.
    """
    mission_id = "RUN-TEST-002"
    claim_id = "NEX-TEST-002"
    
    await mission_manager.create_mission(mission_id=mission_id, claim_id=claim_id)
    
    mock_genai_client = MagicMock()
    mock_response_llm = MagicMock()
    mock_response_llm.text = '{"summary": "Test summary under 120 words.", "human_question": "Is this expense pre-approved?"}'
    mock_genai_client.models.generate_content.side_effect = [
        mock_response_llm,
        Exception("TTS API rate limit exceeded")  # Raises exception on second call (TTS)
    ]

    with patch.object(settings, "GEMINI_API_KEY", "MOCK_KEY"), \
         patch("google.genai.Client", return_value=mock_genai_client):
        packet = await HumanEscalationService.get_or_create_package(mission_id)

        assert isinstance(packet, EscalationPacket)
        assert packet.audio_url is None
        assert packet.audio_duration == 0.0
        assert packet.summary == "Test summary under 120 words."
        assert packet.human_question == "Is this expense pre-approved?"

    await mission_manager.clear_mission(mission_id)


@pytest.mark.anyio
async def test_escalation_graceful_storage_fallback():
    """
    Verifies that if GCS uploading raises an exception, the service gracefully
    saves the audio file locally as a fallback and returns a local mock signed URL.
    """
    mission_id = "RUN-TEST-003"
    claim_id = "NEX-TEST-003"
    
    await mission_manager.create_mission(mission_id=mission_id, claim_id=claim_id)
    
    mock_genai_client = MagicMock()
    mock_response_llm = MagicMock()
    mock_response_llm.text = '{"summary": "Test GCS fallback summary.", "human_question": "Can you verify this receipt?"}'
    mock_response_tts = MagicMock()
    mock_part = MagicMock()
    mock_part.inline_data.data = b"BINARY_AUDIO_BYTES_TEST"
    mock_response_tts.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
    
    mock_genai_client.models.generate_content.side_effect = [
        mock_response_llm,
        mock_response_tts
    ]

    with patch.object(settings, "GEMINI_API_KEY", "MOCK_KEY"), \
         patch("google.genai.Client", return_value=mock_genai_client), \
         patch("app.escalation.storage.settings") as mock_settings, \
         patch("app.escalation.storage.save_audio_locally", return_value="http://localhost:8000/public/audio/RUN-TEST-003.wav") as mock_save_local:
        
        # Force storage client to throw connection exception to trigger local save
        mock_settings.GCS_BUCKET = "my-configured-bucket"
        mock_settings.PORT = 8000
        
        with patch("google.cloud.storage.Client", side_effect=Exception("GCS connection timeout")):
            packet = await HumanEscalationService.get_or_create_package(mission_id)

            assert isinstance(packet, EscalationPacket)
            # Confirms fallback local static route URL is generated
            assert packet.audio_url == "http://localhost:8000/public/audio/RUN-TEST-003.wav"
            mock_save_local.assert_called_once_with(mission_id, b"BINARY_AUDIO_BYTES_TEST")

    await mission_manager.clear_mission(mission_id)


def test_api_escalation_endpoint():
    """
    Verifies the FastAPI REST API route /claims/{mission_id}/escalation.
    Asserts GET response code, payload schema structure, and error 404 behavior.
    """
    # 1. Verify 404 response on missing missions
    response_404 = client.get("/claims/RUN-MISSING-999/escalation")
    assert response_404.status_code == 404
    assert "RUN-MISSING-999" in response_404.json()["detail"]

    # 2. Setup mock mission with cached escalation packet to test endpoint response
    mission_id = "RUN-TEST-004"
    claim_id = "NEX-TEST-004"
    
    async def setup_mission():
        await mission_manager.create_mission(mission_id=mission_id, claim_id=claim_id)
        packet_data = {
            "mission_id": mission_id,
            "claim_id": claim_id,
            "summary": "This is a cached summary.",
            "recommendation": "ESCALATE",
            "human_question": "Cached question?",
            "confidence": 95,
            "decision_reason": "Policy limit override required.",
            "generated_at": "2026-07-11T12:00:00Z"
        }
        await mission_manager.attach_metadata(mission_id, {"escalation_packet": packet_data})

    # Run async setup synchronously using loop helper
    asyncio.run(setup_mission())

    # 3. Test successful GET request
    response_200 = client.get(f"/claims/{mission_id}/escalation")
    assert response_200.status_code == 200
    data = response_200.json()
    assert data["mission_id"] == mission_id
    assert data["summary"] == "This is a cached summary."
    assert data["human_question"] == "Cached question?"
    assert data["confidence"] == 95

    # Cleanup in-memory database
    asyncio.run(mission_manager.clear_mission(mission_id))


def test_api_health_endpoint_integration():
    """
    Verifies that the /health diagnostic endpoint successfully includes
    the human_escalation_status metrics parameter.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "human_escalation_status" in data
    status_block = data["human_escalation_status"]
    assert "tts_status" in status_block
    assert "storage_status" in status_block
    assert "last_tts_generation" in status_block
    assert "last_upload" in status_block
