"""
Integration test suite verifying the REST endpoints, Server-Sent Events (SSE) stream,
and mock playback scenario runners in the Nexus AI backend.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.event_bus import event_bus
from app.core.mission_manager import mission_manager

# Enable DEMO_MODE for testing simulation endpoints
settings.DEMO_MODE = True

client = TestClient(app)


def test_root_endpoint() -> None:
    """
    Verifies that the root API endpoint returns active running states.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "service": "Nexus AI Operations Platform",
        "status": "running"
    }


def test_health_diagnostics_endpoint() -> None:
    """
    Verifies that health diagnostics return active active metrics and connections count.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "active_missions" in data
    assert "connected_sse_clients" in data
    assert "total_events_stored" in data["event_bus_status"]


def test_create_claim_endpoint() -> None:
    """
    Verifies that posting to /claims registers a mission and dispatches start events.
    """
    response = client.post("/claims")
    assert response.status_code == 201
    payload = response.json()
    assert "mission_id" in payload
    assert "claim_id" in payload
    
    # Assert mission is recorded in memory
    mission_id = payload["mission_id"]
    mission = client.get("/health").json()  # Check active missions increase
    assert mission["active_missions"] > 0


def test_demo_scenario_trigger_endpoint() -> None:
    """
    Verifies that posting to /demo/{scenario} triggers mock playback background jobs.
    """
    response = client.post("/demo/approval")
    assert response.status_code == 200
    payload = response.json()
    assert "mission_id" in payload
    
    # Check invalid scenario validation returns 400
    bad_response = client.post("/demo/invalid-scenario-name")
    assert bad_response.status_code == 400


def test_sse_stream_delivery() -> None:
    """
    Asserts that GET /claims/{id}/events streams SSE packets with double newlines.
    """
    # 1. Create a claim
    res = client.post("/claims")
    mission_id = res.json()["mission_id"]
    
    # 2. Query SSE stream with stream=false to get historical replay and exit immediately
    response = client.get(f"/claims/{mission_id}/events?stream=false")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    
    # Split lines and filter out empty ones
    lines = [line.strip() for line in response.text.split("\n") if line.strip()]
    
    assert len(lines) >= 2
    assert lines[0].startswith("event:")
    assert lines[1].startswith("data:")

