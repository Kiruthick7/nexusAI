import asyncio
import random
import os
import re
import time
from typing import Dict, Any, Generator, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File, Request, Response
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import logger, request_id_ctx, mission_id_ctx
from app.core.middleware import TracingAndLoggingMiddleware, claims_rate_limiter, demo_rate_limiter
from app.core.mission_manager import mission_manager
from app.core.event_bus import event_bus
from app.core.event_publisher import publish_workflow_started
from app.services.mock_playback import run_playback_scenario
from app.services.intake_agent import run_intake_agent, DocumentClassificationError
from app.workflow.planner import run_planner_agent
from app.escalation.service import HumanEscalationService, escalation_tracker
from app.escalation.models import EscalationPacket
from app.gemma.service import GemmaIntelligenceService, gemma_tracker
from app.gemma.models import GemmaExplanationPacket


app = FastAPI(
    title="Nexus AI Operations Platform",
    description="Real-Time Event-Driven multi-agent enterprise expense adjudication API.",
    version="1.1.0",
    debug=settings.DEBUG,
)

# Set app start time for uptime diagnostics
app_start_time = time.time()

# Register global contextual tracing middleware first
app.add_middleware(TracingAndLoggingMiddleware)

# Enable CORS to allow local and production frontends to connect seamlessly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Standard HTTP Exception handler returning consistent JSON responses masking internal tracebacks.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "request_id": request_id_ctx.get(),
            "mission_id": mission_id_ctx.get()
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Global unhandled exception fallback handler. Mask tracebacks from API clients.
    """
    logger.error(f"[GLOBAL EXCEPTION] Unhandled exception occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred.",
            "error_code": "INTERNAL_SERVER_ERROR",
            "request_id": request_id_ctx.get(),
            "mission_id": mission_id_ctx.get()
        }
    )


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes upload invoice filenames to safeguard against path traversal vulnerabilities.
    """
    base = os.path.basename(filename)
    return re.sub(r"[^a-zA-Z0-9._-]", "_", base)


# Global counter tracking active real-time SSE stream connections
connected_sse_clients = 0
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
async def read_health() -> Dict[str, Any]:
    """
    Health diagnostic endpoint returning deep operational metrics across all 
    platform services, databases, and AI model pathways.
    """
    start_time = time.perf_counter()
    logger.info("Deep health diagnostics requested.")
    
    # 1. Resolve application metrics
    uptime = time.time() - app_start_time
    total_missions = len(mission_manager._missions)
    total_events = len(event_bus._events)
    active_subscriptions = sum(len(qs) for qs in event_bus._subscriptions.values())
    
    # 2. Sub-system health verification status
    sql_status = "healthy"
    bq_status = "healthy"
    storage_status = "healthy"
    mcp_status = "healthy"
    gemini_status = "healthy"
    
    # In Demo Mode, cloud and API providers default to healthy/mocked
    # In Production, we can check settings or perform quick validation
    if not settings.DEMO_MODE:
        # Check Cloud SQL config presence
        if not settings.CLOUD_SQL_CONNECTION_NAME:
            sql_status = "unconfigured"
        # Check GCS bucket presence
        if not settings.GCS_BUCKET:
            storage_status = "unconfigured"
        # Check BQ presence
        if not settings.BQ_DATASET:
            bq_status = "unconfigured"
        # Check Gemini API Key presence
        if not settings.GEMINI_API_KEY:
            gemini_status = "unconfigured"
            
    # Fetch Human Escalation diagnostics
    escalation_metrics = await escalation_tracker.get_metrics()
    
    # Fetch Gemma diagnostics
    gemma_metrics = await gemma_tracker.get_metrics()
    
    latency = time.perf_counter() - start_time
    
    return {
        # Keep original keys exact for frontend backward compatibility
        "status": "healthy",
        "active_missions": total_missions,
        "connected_sse_clients": connected_sse_clients,
        "event_bus_status": {
            "total_events_stored": total_events,
            "active_subscriptions": active_subscriptions
        },
        "human_escalation_status": escalation_metrics,
        "gemma_status": gemma_metrics,
        
        # Extended Production / Audit keys
        "application": {
            "version": app.version,
            "environment": "demo" if settings.DEMO_MODE else "production",
            "uptime_seconds": uptime,
            "latency_seconds": latency
        },
        "planner": {
            "active_runs": total_missions,
            "status": "idle" if total_missions == 0 else "active"
        },
        "mission_manager": {
            "total_missions_cached": total_missions
        },
        "services_health": {
            "cloud_sql": sql_status,
            "bigquery": bq_status,
            "cloud_storage": storage_status,
            "mcp_connectivity": mcp_status,
            "gemini": gemini_status,
            "gemma": gemma_metrics.get("status", "healthy")
        },
        "version": app.version,
        "environment": "demo" if settings.DEMO_MODE else "production",
        "latency": f"{latency * 1000:.2f}ms",
        "uptime": f"{uptime:.2f}s"
    }


@app.get("/ready")
async def read_ready() -> Response:
    """
    Shallow and deep readiness checks verifying settings, database clients, 
    and AI Studio integration gateways.
    """
    is_ready = True
    details = {}
    
    # 1. Config validation
    required_vars = [
        "GOOGLE_API_KEY",
        "MODEL_NAME",
        "MODEL_NAME_TTS",
        "MODEL_NAME_LIVE",
        "MODEL_NAME_TRANSLATE",
        "MODEL_NAME_IMAGE",
        "MODEL_NAME_OMNI",
        "INTERACTIONS_MODEL",
        "GEMMA_MODEL",
        "GCP_PROJECT_ID",
        "BQ_DATASET",
        "GCS_BUCKET",
        "CLOUD_SQL_CONNECTION_NAME",
        "CLOUD_SQL_DATABASE",
        "CLOUD_SQL_USER",
        "CLOUD_SQL_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
            
    if missing_vars:
        # If in DEMO_MODE, missing variables are allowed!
        if not settings.DEMO_MODE:
            is_ready = False
            details["config"] = f"Missing settings: {', '.join(missing_vars)}"
            
    if is_ready:
        return Response(content="READY", media_type="text/plain", status_code=200)
    else:
        return Response(
            content=f"NOT_READY - {details.get('config', 'Unconfigured services')}", 
            media_type="text/plain", 
            status_code=503
        )


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
    except DocumentClassificationError as e:
        logger.warning(f"[ORCHESTRATOR] Ingestion rejected due to document classification: {e}")
        from app.models.enums import WorkflowStatus, EventType, AgentName, AgentStatus, Severity
        from app.core.event_publisher import _create_base_event
        
        # Transition mission to FAILED/REJECTED states
        await mission_manager.update_workflow_status(mission_id, WorkflowStatus.FAILED)
        await mission_manager.update_stage(mission_id, "REJECTED")
        
        # Publish final decision event with REJECT status
        rejection_event = _create_base_event(
            mission_id=mission_id,
            event_type=EventType.DECISION_COMPLETED,
            agent=AgentName.ARBITER,
            status=AgentStatus.ERROR,
            title="Document Ingestion Rejected",
            message=f"Validation failed. Reason: {str(e)}",
            severity=Severity.ERROR,
            metadata={
                "decision_packet": {
                    "mission": mission_id,
                    "recommendation": "REJECT",
                    "reason": f"Ingestion Gate Filter: {str(e)}",
                    "confidence": 0.0,
                    "conflicts": [],
                    "resolution_summary": "Orchestration bypassed. File was classified as non-invoice or non-receipt content.",
                    "human_question": None,
                    "timeline": [{"agent": "INTAKE", "title": "Ingestion Gate Filter", "status": "failed", "message": str(e)}],
                    "audit_summary": {
                        "is_complete": True,
                        "error": f"Document rejected: {str(e)}"
                    }
                }
            }
        )
        await event_bus.publish(rejection_event)
    except Exception as e:
        logger.error(f"[ORCHESTRATOR] Critical execution failure in workflow loop: {e}", exc_info=True)


@app.post("/claims", status_code=201)
async def create_claim(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = None
) -> Dict[str, str]:
    """
    Creates a new adjudication Mission, generating tracking IDs and initializing states.
    Dispatches the orchestration workflow task to run both Intake and Planner agents in the background.
    """
    # 1. Sliding Window Rate Limiter
    client_ip = request.client.host if request.client else "unknown"
    if not claims_rate_limiter.is_allowed(client_ip):
        logger.warning(f"[RATE LIMIT] Blocked claim ingestion from client IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Too many claim submissions. Please wait before retrying.")
        
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
        
        # 2. File Size validation (Max 5MB)
        if len(file_bytes) > 5 * 1024 * 1024:
            logger.warning(f"[SECURITY] Upload file size exceeds 5MB limit ({len(file_bytes)} bytes) for mission {mission_id}")
            raise HTTPException(status_code=400, detail="File size exceeds the maximum 5MB limit.")
            
        # 3. File MIME type validation (PDF, PNG, JPEG only)
        mime_type = file.content_type
        if mime_type not in ["application/pdf", "image/png", "image/jpeg"]:
            logger.warning(f"[SECURITY] Rejected unsupported upload MIME type '{mime_type}' for mission {mission_id}")
            raise HTTPException(status_code=400, detail="Unsupported file format. Only PDF, PNG, and JPEG files are allowed.")
            
        filename = sanitize_filename(file.filename or "invoice.png")
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
async def trigger_demo_scenario(
    scenario: str,
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    Triggers a background simulation of a specific multi-agent orchestration scenario.
    
    Supported scenarios:
        - approval
        - fraud
        - injection
        - conflict
    """
    # 1. Enforce DEMO_MODE restriction
    if not settings.DEMO_MODE:
        logger.warning(f"[SECURITY] Production client attempted to access demo simulation endpoint: {request.url.path}")
        raise HTTPException(
            status_code=403,
            detail="Demo simulation endpoints are disabled in production environment."
        )
        
    # 2. Sliding Window Rate Limiter
    client_ip = request.client.host if request.client else "unknown"
    if not demo_rate_limiter.is_allowed(client_ip):
        logger.warning(f"[RATE LIMIT] Blocked demo simulation request from client IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Too many simulation requests. Please wait before retrying.")
        
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


@app.get("/claims/{mission_id}/escalation", response_model=EscalationPacket)
async def get_claim_escalation(mission_id: str) -> EscalationPacket:
    """
    Exposes the Human Escalation package compilation REST endpoint.
    Retrieves or creates the premium EscalationPacket for the given mission.
    """
    logger.info(f"[API] Requested escalation package for mission_id={mission_id}")
    try:
        packet = await HumanEscalationService.get_or_create_package(mission_id)
        return packet
    except ValueError as err:
        logger.warning(f"[API] Escalation package request rejected: {err}")
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as err:
        logger.error(f"[API] Failed to get or create escalation package: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error assembling escalation package.")


@app.get("/claims/{mission_id}/explanation", response_model=GemmaExplanationPacket)
async def get_claim_explanation(mission_id: str) -> GemmaExplanationPacket:
    """
    Exposes the Gemma explainability analysis package REST endpoint.
    Retrieves cached package or dynamically generates a fresh explanation using Gemma.
    """
    logger.info(f"[API] Requested explanation package for mission_id={mission_id}")
    try:
        packet = await GemmaIntelligenceService.get_or_create_explanation(mission_id)
        return packet
    except ValueError as err:
        logger.warning(f"[API] Explanation request rejected: {err}")
        raise HTTPException(status_code=404, detail=str(err))
    except Exception as err:
        logger.error(f"[API] Failed to generate claim explanation: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error assembling claim explanation.")


@app.get("/public/audio/{filename}")
def get_public_audio(filename: str) -> FileResponse:
    """
    Serves synthesized local briefing audio files using FastAPI FileResponse.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "public", "audio", filename)
    
    # Security/existence checks
    if not os.path.exists(file_path):
        logger.warning(f"[API] Audio file not found: {filename}")
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    return FileResponse(file_path, media_type="audio/wav", filename=filename)
