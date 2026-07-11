# Nexus AI - Backend Service Module

The **Nexus AI Backend Service Module** is a high-performance, stateless, event-driven web application built with **FastAPI (Python 3.12)**. It orchestrates multi-agent claim validation topologies, aggregates structured evidence, evaluates deterministic safety gates, synthesizes human escalation briefing audio, and registers independent Gemma audit explanations. All pipeline telemetry is pushed dynamically to clients via Server-Sent Events (SSE).

---

## 🏛️ Architecture & Component Design

The backend uses a strictly modular design with a decoupled execution flow:

```text
Uvicorn Gateway (FastAPI)
  ├── TracingAndLoggingMiddleware (Request Tracking X-Request-ID & contextvars)
  ├── RateLimitingMiddleware (IP sliding-window boundary limits)
  └── REST Controllers / SSE Event Channels
        ├── POST /claims ➔ Dispatches non-blocking BackgroundTask
        ├── GET /claims/{mission_id}/events ➔ Pipes EventBus SSE stream
        └── GET /health & GET /ready ➔ Returns system telemetry & diagnostic states
```

Once a claim is received, the orchestration pipeline is executed in a background thread to keep the endpoint non-blocking:

### 🤖 Core Autonomous Agents & Core Services

#### 1. Intake Agent (`app/workflow/planner.py`)
- **Responsibility**: Ingests unstructured invoices, extracts key fields (Claim ID, Employee Name, Item Costs, Provider GSTIN), compiles standard Pydantic models, and registers the initial mission state.
- **LLM Engine**: Gemini 3.5 Flash (via Google GenAI SDK).

#### 2. Planner Agent (`app/workflow/planner.py`)
- **Responsibility**: Builds a customized topological task execution graph based on claim context. Determines which specialist validation pathways must run.
- **LLM Engine**: Gemini 3.5 Flash.

#### 3. Parallel Specialists Pool (`app/workflow/executor.py`)
Run concurrently inside an asynchronous thread-pool executor:
- **Provider Agent**: Validates practitioner active registration and GSTIN validity. It maps to external registries using dynamic Model Context Protocol (MCP) connectors.
- **Policy Agent**: Validates item amounts against standard company reimbursement rules, medical/dental codes, and category allowance limits.
- **Pattern Agent**: Performs behavioral fraud audits, scanning historical claims to identify duplicate submissions, billing clusters, or split-billing patterns.

#### 4. Arbiter Decision Engine (`app/arbiter/`)
- **Aggregator (`aggregator.py`)**: Combines multi-agent findings and signs of completion.
- **Resolver (`resolver.py`)**: Identifies logical conflict boundaries. It executes a conflict resolution round using pre-defined specialist authority weights (e.g., Pattern overrides Provider on risk limits).
- **Decision Engine (`decision_engine.py`)**: Formulates the final recommendation (`APPROVE`, `REJECT`, `ESCALATE`). It evaluates physical **Tool Gates** (circuit breakers) in `gates.py` and publishes a standardized `DecisionPacket`.

#### 5. Human Escalation Service (`app/escalation/`)
- **Responsibility**: Invoked when Arbiter recommends `ESCALATE`. It compiles a review package, structures an actionable human override questionnaire, and synthesizes a spoken `.wav` audio brief.
- **TTS Engine**: Gemini 3.1 Flash Text-to-Speech Preview (using `VoiceConfig` prebuilt Kore voice).
- **Fallback storage**: Uploads to Google Cloud Storage (GCS). If connection fails, it falls back to saving locally inside `/public/audio/` and returns local signed path URLs.

#### 6. Gemma Intelligence Service (`app/gemma/`)
- **Responsibility**: An independent, out-of-band audit layer. It checks decision consistency, flags potential logical discrepancies in the Arbiter's reasoning, and drafts friendly, transparent summaries (Executive, Financial, Employee, Technical) to build absolute human trust.
- **LLM Engine**: Gemma 2 27B IT (via Google AI Studio).

---

## ⚙️ Environment Configuration & Startup Guards

Settings are centralized inside `app/core/config.py` using Pydantic `BaseSettings`, loading from `.env`:

| Variable Name | Description | Default Value / Template |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google AI Studio API access key | `your_api_key` |
| `GOOGLE_API_KEY` | Google services fallback key | `your_api_key` |
| `MODEL_NAME` | Primary LLM orchestrator | `gemini-3.5-flash` |
| `MODEL_NAME_TTS` | Spoken synthesis model | `gemini-3.1-flash-tts-preview` |
| `GEMMA_MODEL` | Independent explainer model | `gemma2-27b-it` |
| `DEMO_MODE` | Bypasses live external GCP integrations | `true` |
| `PORT` | Local service port allocation | `8000` |

### 🔒 Startup Fail-Fast Guardrail
When the backend starts, `validate_startup_config()` checks all 16 target environmental variables:
- **`DEMO_MODE=true`**: Missing keys log prominent amber warning banners but allow the server to run (crucial for offline local demonstrations).
- **`DEMO_MODE=false`**: Missing keys crash the server instantly (`sys.exit(1)`), preventing dirty runtime failure cascades in staging/production environments.

---

## 📡 API Specification & SSE Events

### 📥 Claim Ingestion
`POST /claims`
- **Enforced Security Limits**: Maximum payload size is **5MB**. Supported MIME types are `application/pdf`, `image/png`, and `image/jpeg`.
- **Malicious Traversal Filter**: Files sanitize inputs via `sanitize_filename()` before storing to prevent path-traversal injections.
- **Response**: Returns alphanumeric `mission_id` and `claim_id` parameters.

### 🔄 SSE Real-time Streaming
`GET /claims/{mission_id}/events`
- **Protocol**: Standard non-blocking `text/event-stream` connection.
- **Events Published**:
  - `intake_started` ➔ `intake_completed`
  - `planner_started` ➔ `planner_completed`
  - `provider_started` ➔ `provider_completed`
  - `policy_started` ➔ `policy_completed`
  - `pattern_started` ➔ `pattern_completed`
  - `arbiter_started` ➔ `evidence_aggregation_started` ➔ `conflict_detected` ➔ `resolution_round_started` ➔ `resolution_completed` ➔ `decision_recommended` ➔ `decision_completed`
  - `escalation_started` ➔ `summary_generated` ➔ `human_question_generated` ➔ `tts_started` ➔ `tts_completed` ➔ `audio_uploaded` ➔ `escalation_completed`
  - `gemma_started` ➔ `gemma_summary_generated` ➔ `gemma_review_completed` ➔ `gemma_completed`

### 🏥 System Diagnostics
`GET /health`
- **Metrics**: Dynamic checks verifying database ping, bucket existence, memory-registers, active SSE listeners, and model gateway connection status.

`GET /ready`
- **Purpose**: Low-latency readiness checkpoint return `200 READY` to GCP Cloud Run load balancers.

---

## 🧪 Running the Tests

Headless integration and Pydantic validation tests are implemented with `pytest`.

To run tests with environment guardrails bypassed:
```bash
DEMO_MODE=true backend/.venv/bin/pytest backend/tests/
```

To run a specific test file (e.g., verifying Gemma logic):
```bash
DEMO_MODE=true backend/.venv/bin/pytest backend/tests/test_gemma_service.py
```

---

## 🐳 Dockerization & Cloud Deployment

### Multi-stage Docker Container (`Dockerfile`)
The backend is packaged inside a highly-optimized multi-stage container leveraging Astral's `uv` tool for speed and layer cache efficiency:
- **Build stage**: Compiles requirements and builds local caches.
- **Runtime stage**: Uses official slim-Python images, copying only verified source runtimes, keeping final deployment images small and fast to scale.

### Deploying to Google Cloud Run
Deployments are automated inside `backend/scripts/deploy_cloud_run.sh`:
```bash
cd backend
chmod +x scripts/deploy_cloud_run.sh
./scripts/deploy_cloud_run.sh
```
This script handles Google Artifact Registry compiles, Cloud SQL postgres associations, GCS cloud storage configurations, and launches the Cloud Run service.
