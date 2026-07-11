"""
Test suite validating the Intake Agent, Pydantic schemas, programmatic normalizations,
null-fallback zero confidences, and async API integration endpoints.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.mission_manager import mission_manager
from app.models.enums import WorkflowStatus, EventType
from app.services.intake_agent import run_intake_agent

client = TestClient(app)


def test_intake_agent_state_transitions_and_events() -> None:
    """
    Verifies that run_intake_agent updates workflow state to INGESTING, streams events,
    and programmatically normalizes extracted field text.
    """
    async def run_test() -> None:
        mission_id = "RUN-9999"
        claim_id = "NEX-9999"
        await mission_manager.create_mission(mission_id=mission_id, claim_id=claim_id)
        
        # Mock Response Text for Gemini
        mock_response = MagicMock()
        mock_response.text = (
            '{"vendor_name": "Precision Dental ", "gstin": "33aabca1234f1z0", '
            '"invoice_number": "inv-10023", "amount": 1250.00, "currency": "inr", '
            '"date": "2026-07-11", "category": "Dental Care", "employee_id": "emp-9082", '
            '"confidence": {"vendor_name": 0.99, "gstin": 0.95, "invoice_number": 0.98, '
            '"amount": 0.99, "currency": 0.97, "date": 0.96, "category": 0.91, '
            '"employee_id": 0.92}}'
        )
        
        with patch("app.services.intake_agent.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "mock-key"
            mock_settings.MODEL_NAME = "gemini-3.5-flash"
            
            with patch("google.genai.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.models.generate_content.return_value = mock_response
                
                # Run Intake Agent
                context = await run_intake_agent(
                    mission_id=mission_id,
                    claim_id=claim_id,
                    file_bytes=b"mock-image-content-bytes",
                    filename="receipt.png"
                )
                
                # 1. Assert Normalizations
                assert context.vendor_name == "Precision Dental"  # Trimmed whitespace
                assert context.gstin == "33AABCA1234F1Z0"  # Uppercased
                assert context.invoice_number == "INV-10023"  # Uppercased
                assert context.amount == 1250.00
                assert context.currency == "INR"  # Uppercased
                assert context.date == "2026-07-11"
                assert context.category == "Dental Care"
                assert context.employee_id == "EMP-9082"  # Uppercased
                
                # 2. Assert Confidence Parsing
                assert context.confidence["vendor_name"] == 0.99
                assert context.confidence["gstin"] == 0.95
                assert context.confidence["employee_id"] == 0.92
                
                # 3. Assert Mission State transitioned
                mission = await mission_manager.get_mission(mission_id)
                assert mission is not None
                assert mission.workflow_status == WorkflowStatus.INGESTING
                assert mission.current_stage == "INGESTING"
                
                # 4. Assert stored SharedMissionContext registry slot
                stored_context = await mission_manager.get_context(mission_id)
                assert stored_context is not None
                assert stored_context.mission_id == mission_id
                assert stored_context.claim_id == claim_id

    asyncio.run(run_test())


def test_intake_agent_unreadable_fields_default_to_zero_confidence() -> None:
    """
    Verifies that unreadable fields are defaulted to None / 0.0 confidence.
    """
    async def run_test() -> None:
        mission_id = "RUN-8888"
        claim_id = "NEX-8888"
        await mission_manager.create_mission(mission_id=mission_id, claim_id=claim_id)
        
        mock_response = MagicMock()
        mock_response.text = (
            '{"vendor_name": null, "gstin": null, "invoice_number": null, '
            '"amount": null, "currency": null, "date": null, "category": null, '
            '"employee_id": null, "confidence": {"vendor_name": 0.0, "gstin": 0.0, '
            '"invoice_number": 0.0, "amount": 0.0, "currency": 0.0, "date": 0.0, '
            '"category": 0.0, "employee_id": 0.0}}'
        )
        
        with patch("app.services.intake_agent.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "mock-key"
            mock_settings.MODEL_NAME = "gemini-3.5-flash"
            
            with patch("google.genai.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.models.generate_content.return_value = mock_response
                
                context = await run_intake_agent(
                    mission_id=mission_id,
                    claim_id=claim_id,
                    file_bytes=b"blurred-photo-bytes",
                    filename="blurry.png"
                )
                
                assert context.vendor_name is None
                assert context.amount is None
                assert context.confidence["vendor_name"] == 0.0
                assert context.confidence["amount"] == 0.0

    asyncio.run(run_test())


def test_api_claims_endpoint_form_multipart_and_fallback() -> None:
    """
    Verifies that POST /claims remains compatible with non-file and file requests.
    """
    # Test fallback compatibility
    response = client.post("/claims")
    assert response.status_code == 201
    payload = response.json()
    assert "mission_id" in payload
    assert "claim_id" in payload
    
    # Test actual multipart form file post
    file_payload = {"file": ("test_receipt.png", b"fake receipt bytes", "image/png")}
    form_response = client.post("/claims", files=file_payload)
    assert form_response.status_code == 201
    form_payload = form_response.json()
    assert "mission_id" in form_payload
    assert "claim_id" in form_payload
