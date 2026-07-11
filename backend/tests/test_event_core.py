"""
Unit test suite verifying the Event-Driven Core Architecture of Nexus AI.

Tests mission creation, async event publishing, chronological replay ordering,
isolation of multiple missions, and concurrency lock safety using asyncio.run.
"""

import asyncio
from datetime import datetime, timezone, timedelta
import pytest
from app.models.enums import WorkflowStatus, AgentName, AgentStatus, Severity, EventType
from app.core.mission_manager import mission_manager
from app.core.event_bus import event_bus
from app.core.event_publisher import (
    publish_workflow_started,
    publish_agent_started,
    publish_agent_completed,
    publish_conflict,
    publish_gate_check,
    publish_decision,
    publish_workflow_completed,
)


def test_mission_lifecycle_management() -> None:
    """
    Asserts that MissionManager correctly creates missions and handles state transitions.
    """
    async def run_test() -> None:
        mission_id = "RUN-1111"
        claim_id = "CLAIM-2222"
        
        # 1. Create Mission
        mission = await mission_manager.create_mission(mission_id, claim_id, {"source": "test"})
        assert mission.mission_id == mission_id
        assert mission.claim_id == claim_id
        assert mission.workflow_status == WorkflowStatus.IDLE
        assert mission.current_stage == "IDLE"
        assert mission.metadata["source"] == "test"
        
        # 2. Update Stage
        updated = await mission_manager.update_stage(mission_id, "INGESTING")
        assert updated is not None
        assert updated.current_stage == "INGESTING"
        
        # 3. Update Status
        updated = await mission_manager.update_workflow_status(mission_id, WorkflowStatus.INGESTING)
        assert updated is not None
        assert updated.workflow_status == WorkflowStatus.INGESTING
        
        # 4. Attach Metadata
        updated = await mission_manager.attach_metadata(mission_id, {"ocr_cleared": True})
        assert updated is not None
        assert updated.metadata["source"] == "test"
        assert updated.metadata["ocr_cleared"] is True
        
        # 5. Retrieve Mission
        retrieved = await mission_manager.get_mission(mission_id)
        assert retrieved is not None
        assert retrieved.mission_id == mission_id
        assert retrieved.current_stage == "INGESTING"
        
        # Cleanup
        await mission_manager.clear_mission(mission_id)
        assert await mission_manager.get_mission(mission_id) is None

    asyncio.run(run_test())


def test_event_publishing_and_replay() -> None:
    """
    Asserts that events published to the EventBus are stored, subscribable, and replayable.
    """
    async def run_test() -> None:
        mission_id = "RUN-3333"
        await event_bus.clear_mission(mission_id)
        
        # 1. Subscribe to mission events in real-time
        queue = await event_bus.subscribe(mission_id)
        
        # 2. Publish starting event using helper
        evt1 = await publish_workflow_started(mission_id, message="Test started")
        
        # Verify subscriber receives the event
        received_evt = queue.get_nowait()
        assert received_evt.event_id == evt1.event_id
        assert received_evt.event_type == EventType.WORKFLOW_STARTED
        
        # 3. Publish secondary agent events
        evt2 = await publish_agent_started(
            mission_id,
            agent=AgentName.PLANNER,
            event_type=EventType.PLANNER_STARTED,
            title="Planner Launching",
            message="Planner executing initial routing"
        )
        
        evt3 = await publish_agent_completed(
            mission_id,
            agent=AgentName.PLANNER,
            event_type=EventType.PLANNER_DISPATCH,
            status=AgentStatus.SUCCESS,
            title="Planner Dispatched",
            message="Orchestration mapped",
            latency_ms=45,
            tools_used=["get_claim_context"]
        )
        
        # 4. Replay and verify chronological ordering
        history = await event_bus.replay_events(mission_id)
        assert len(history) == 3
        assert history[0].event_id == evt1.event_id
        assert history[1].event_id == evt2.event_id
        assert history[2].event_id == evt3.event_id
        
        # Cleanup
        await event_bus.unsubscribe(mission_id, queue)
        await event_bus.clear_mission(mission_id)

    asyncio.run(run_test())


def test_multiple_missions_isolation() -> None:
    """
    Asserts that separate missions do not leak events or states between each other.
    """
    async def run_test() -> None:
        m1 = "RUN-AAAA"
        m2 = "RUN-BBBB"
        
        await event_bus.clear_mission(m1)
        await event_bus.clear_mission(m2)
        
        # Publish events to both missions
        await publish_workflow_started(m1, message="M1 Initialized")
        await publish_workflow_started(m2, message="M2 Initialized")
        await publish_agent_started(m1, AgentName.PROVIDER, EventType.PROVIDER_STARTED, "Prov", "Start")
        
        # Replay M1 and M2
        h1 = await event_bus.replay_events(m1)
        h2 = await event_bus.replay_events(m2)
        
        assert len(h1) == 2
        assert len(h2) == 1
        assert all(e.mission_id == m1 for e in h1)
        assert all(e.mission_id == m2 for e in h2)
        
        # Cleanup
        await event_bus.clear_mission(m1)
        await event_bus.clear_mission(m2)

    asyncio.run(run_test())


def test_chronological_replay_ordering() -> None:
    """
    Asserts that the replay method strictly sorts events chronologically by timestamp.
    """
    async def run_test() -> None:
        mission_id = "RUN-SORT"
        await event_bus.clear_mission(mission_id)
        
        # Manually publish events with artificially forced timestamps out of insertion order
        evt_future = await publish_workflow_started(mission_id, message="Future event")
        evt_past = await publish_workflow_completed(mission_id, message="Past event")
        
        # Manually alter timestamps for verification
        evt_past.timestamp = datetime.now(timezone.utc) - timedelta(hours=1)
        evt_future.timestamp = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Replay
        replayed = await event_bus.replay_events(mission_id)
        assert replayed[0].event_id == evt_past.event_id
        assert replayed[1].event_id == evt_future.event_id
        
        # Cleanup
        await event_bus.clear_mission(mission_id)

    asyncio.run(run_test())


def test_concurrent_publishing_safety() -> None:
    """
    Asserts thread and task lock safety under heavy concurrent publishing loads.
    """
    async def run_test() -> None:
        mission_id = "RUN-CONCUR"
        await event_bus.clear_mission(mission_id)
        
        # Define concurrent publisher worker
        async def publish_worker(index: int) -> None:
            await publish_agent_started(
                mission_id,
                agent=AgentName.PROVIDER,
                event_type=EventType.PROVIDER_STARTED,
                title=f"Worker {index}",
                message="Reporting active state"
            )
            
        # Spawn 50 parallel asynchronous tasks
        tasks = [publish_worker(i) for i in range(50)]
        await asyncio.gather(*tasks)
        
        # Verify 50 events registered successfully
        history = await event_bus.replay_events(mission_id)
        assert len(history) == 50
        
        # Cleanup
        await event_bus.clear_mission(mission_id)

    asyncio.run(run_test())
