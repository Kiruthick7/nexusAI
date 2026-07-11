"""
Main bootstrap module instantiating the FastAPI application.

Exposes REST routes for claim creation, real-time Server-Sent Events (SSE) streaming,
and triggering high-fidelity mock playback scenarios.
"""

import asyncio
import random
from typing import Dict, Any, Generator, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import logger
from app.core.mission_manager import mission_manager
from app.core.event_bus import event_bus
from app.core.event_publisher import publish_workflow_started
from app.services.mock_playback import run_playback_scenario
from app.services.intake_agent import run_intake_agent
from app.workflow.planner import run_planner_agent


app = FastAPI(
    title="Nexus AI Operations Platform",
    description="Real-Time Event-Driven multi-agent enterprise expense adjudication API.",
    version="1.1.0",
    debug=settings.DEBUG,
)

# Enable CORS to allow local and production frontends to connect seamlessly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global counter tracking active real-time SSE stream connections
connected_sse_clients = 0


@app.get("/")
def read_root() -> Dict[str, str]:
    """
    Root endpoint verifying server active session states.
    """
    logger.debug("Root path GET '/' requested.")
    return {
        "service": "Nexus AI Operations Platform",
        "status": "running"
    }


@app.get("/health")
def read_health() -> Dict[str, Any]:
    """
    Health diagnostic endpoint returning active system metrics, active missions count,
    connected SSE clients, and EventBus status parameters.
    """
    logger.info("Health diagnostics requested.")
    
    # Safely retrieve metrics from memory
    total_missions = len(mission_manager._missions)
    total_events = len(event_bus._events)
    active_subscriptions = sum(len(qs) for qs in event_bus._subscriptions.values())
    
    return {
        "status": "healthy",
        "active_missions": total_missions,
        "connected_sse_clients": connected_sse_clients,
        "event_bus_status": {
            "total_events_stored": total_events,
            "active_subscriptions": active_subscriptions
        }
    }


async def run_orchestration_workflow(mission_id: str, claim_id: str, file_bytes: bytes, filename: str) -> None:
    """
    Unified background workflow execution loop chaining the Intake Agent and Planner Agent sequentially.
    """
    try:
        # Step 1: Execute Intake Agent OCR Extraction
        context = await run_intake_agent(
            mission_id=mission_id,
            claim_id=claim_id,
            file_bytes=file_bytes,
            filename=filename
        )
        
        # Step 2: Execute Planner Agent Orchestration
        await run_planner_agent(
            mission_id=mission_id,
            claim_id=claim_id,
            context=context
        )
    except Exception as e:
        logger.error(f"[ORCHESTRATOR] Critical execution failure in workflow loop: {e}", exc_info=True)


@app.post("/claims", status_code=201)
async def create_claim(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = None
) -> Dict[str, str]:
    """
    Creates a new adjudication Mission, generating tracking IDs and initializing states.
    Dispatches the orchestration workflow task to run both Intake and Planner agents in the background.
    """
    # Generate sequential or randomized alphanumeric tracking identifiers
    num = random.randint(1000, 9999)
    mission_id = f"RUN-{num}"
    claim_id = f"NEX-{num}"
    
    # Store mission state
    await mission_manager.create_mission(mission_id=mission_id, claim_id=claim_id)
    
    # Immediately dispatch workflow_started event to initialize the stream
    await publish_workflow_started(
        mission_id=mission_id,
        title="Workflow Initialized",
        message=f"Platform orchestration initialized for Claim {claim_id}"
    )
    
    # Read file bytes and run Intake Agent in background
    if file:
        file_bytes = await file.read()
        filename = file.filename or "invoice.png"
    else:
        # Fallback empty bytes and default name if none uploaded
        file_bytes = b""
        filename = "invoice.png"
        
    background_tasks.add_task(
        run_orchestration_workflow,
        mission_id=mission_id,
        claim_id=claim_id,
        file_bytes=file_bytes,
        filename=filename
    )
    
    logger.info(f"[API] Initialized claim and dispatched orchestration workflow for mission_id={mission_id}")
    return {
        "mission_id": mission_id,
        "claim_id": claim_id
    }


@app.get("/claims/{mission_id}/events")
async def stream_events(mission_id: str, stream: bool = True) -> StreamingResponse:
    """
    Exposes a real-time Server-Sent Events (SSE) streaming pipeline for a specific mission.
    
    Supports:
    - Multi-client subscription.
    - Historical event catchup replay upon connection/reconnect.
    - Clean client disconnection cleanup.
    """
    mission = await mission_manager.get_mission(mission_id)
    if not mission:
        logger.warning(f"[SSE] Subscription rejected for missing mission_id={mission_id}")
        raise HTTPException(status_code=404, detail="Mission not found")

    async def event_generator() -> Generator[str, None, None]:
        global connected_sse_clients
        # Increment active client registry counter
        connected_sse_clients += 1
        logger.info(f"[SSE] Client connected. Total active clients: {connected_sse_clients}")
        
        # Subscribe to new real-time events before catching up to avoid race condition gaps
        queue = await event_bus.subscribe(mission_id)
        
        try:
            # 1. Replay and stream historical events first (assures seamless reconnects)
            history = await event_bus.replay_events(mission_id)
            for old_event in history:
                yield f"event: message\ndata: {old_event.model_dump_json()}\n\n"
                
            # 2. Infinite loop awaiting real-time events published to the queue
            if stream:
                while True:
                    new_event = await queue.get()
                    yield f"event: message\ndata: {new_event.model_dump_json()}\n\n"
                    queue.task_done()
                
        except asyncio.CancelledError:
            logger.info(f"[SSE] Client subscription cancelled for mission_id={mission_id}")
            
        finally:
            # Cleanup subscriber queues to prevent memory leaks
            await event_bus.unsubscribe(mission_id, queue)
            connected_sse_clients -= 1
            logger.info(f"[SSE] Client disconnected. Total active clients: {connected_sse_clients}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@app.post("/demo/{scenario}")
async def trigger_demo_scenario(scenario: str, background_tasks: BackgroundTasks) -> Dict[str, str]:
    """
    Triggers a background simulation of a specific multi-agent orchestration scenario.
    
    Supported scenarios:
        - approval
        - fraud
        - injection
        - conflict
    """
    normalized_scenario = scenario.lower().strip()
    if normalized_scenario not in ["approval", "fraud", "injection", "conflict"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario '{scenario}'. Must be 'approval', 'fraud', 'injection', or 'conflict'."
        )
        
    num = random.randint(1000, 9999)
    mission_id = f"RUN-{num}"
    claim_id = f"NEX-{num}"
    
    # Store mission metadata
    await mission_manager.create_mission(mission_id=mission_id, claim_id=claim_id, metadata={"scenario": normalized_scenario})
    
    # Initialize session start event
    await publish_workflow_started(
        mission_id=mission_id,
        title="Simulation Initialized",
        message=f"Starting mock playback for scenario '{normalized_scenario}'"
    )
    
    # Dispatch non-blocking playback sequence to background workers
    background_tasks.add_task(run_playback_scenario, normalized_scenario, mission_id)
    
    logger.info(f"[API] Triggered background scenario='{normalized_scenario}' for mission_id={mission_id}")
    return {
        "mission_id": mission_id
    }
