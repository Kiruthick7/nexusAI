# Nexus AI Operations Platform

> **The Multi-Agent Orchestration & Decision Intelligence Engine for Autonomous Claim Adjudication.**

Welcome to the **Nexus AI Operations Platform**, a state-of-the-art enterprise-grade multi-agent platform designed to automate, audit, and optimize complex claims processing. Powered by **Google Gemini** models and independent **Gemma** intelligence layers, Nexus AI translates raw invoice documents into deterministic adjudications through a coordinated, parallelized, and highly explainable multi-agent system.

---

## 🏛️ System Architecture

The Nexus AI platform is engineered using a **Stateless Event-Driven Decoupled Architecture**. Claims undergo multi-stage topological orchestration while publishing real-time telemetry back to the client via Server-Sent Events (SSE).

```mermaid
graph TD
    Client["Client Dashboard (React/Next.js)"]
    API["FastAPI Gateway (Uvicorn)"]
    DB[("Mission Database (In-Memory / PostgreSQL)")]
    Bus["Central Event Bus (SSE Publisher)"]
    
    Intake["Intake Agent (Document Parser)"]
    Planner["Planner Agent (Orchestration Graph)"]
    
    subgraph Specialists ["Parallel Specialist Pool"]
        Provider["Provider Agent (Ledger Check)"]
        Policy["Policy Agent (Limit Enforcer)"]
        Pattern["Pattern Agent (Risk Scanner)"]
    end
    
    Arbiter["Arbiter Decision Engine"]
    Resolver["Evidence Resolver (Conflict & Weights)"]
    Gates["Tool Gates (Circuit Breakers)"]
    
    Gemma["Gemma Intelligence Layer (Out-of-Band Audit)"]
    Escalate["Human Escalation Service (Briefing Synthesis)"]

    %% Flow arrows
    Client -->|1. POST /claims invoice| API
    Client -->|2. GET /events SSE stream| Bus
    API -->|Launch Thread| Intake
    Intake -->|Extract metadata| DB
    Intake -->|Triggers| Planner
    
    Planner -->|Compiles topological graph| DB
    Planner -->|Schedules concurrent execution| Specialists
    
    Specialists -->|3. Publish findings| Bus
    Specialists -->|Write evidence| DB
    
    Arbiter -->|4. Consume evidence bundle| DB
    Arbiter -->|5. Aggregate & Resolve| Resolver
    Resolver -->|6. Apply Decision Protocol| Arbiter
    Arbiter -->|7. Security Check| Gates
    
    Arbiter -->|8. Recommend APPROVE / REJECT / ESCALATE| Bus
    Arbiter -->|Write DecisionPacket| DB
    
    Arbiter -->|If ESCALATE| Escalate
    Escalate -->|Compile brief & synthesize audio| Bus
    
    Arbiter -->|Out-of-band audit trigger| Gemma
    Gemma -->|Consistency check & explanations| Bus
```

### 🔁 Execution Pipeline Flow
1. **Ingestion**: The client uploads an invoice to `POST /claims`. The gateway enforces strict size (5MB), MIME types (PDF, PNG, JPEG), and sanitizes filenames.
2. **Streaming Event Connection**: The client initiates an asynchronous `GET /claims/{mission_id}/events` SSE streaming connection to capture real-time pipeline status updates.
3. **Parsing**: The **Intake Agent** parses invoice texts, structures metadata parameters, and stores initial payloads in the Mission Database.
4. **Planning**: The **Planner Agent** compiles a dynamic, customized execution graph using Gemini, determining which specialist agents are required to address this specific claim type.
5. **Parallel Validation**: A multi-threaded **WorkflowExecutor** dispatches required specialists:
   - **Provider Agent**: Connects to registries (via MCP tool connectors) to verify credentials.
   - **Policy Agent**: Scans company rules to verify limits, dental/medical codes, and procedural constraints.
   - **Pattern Agent**: Runs behavioral historical checks to detect duplicate billings or split-billing fraud alerts.
6. **Consensus Arbitration**: The **Arbiter Decision Engine** consumes the aggregated evidence bundle. It executes logical conflict resolutions (applying credibility weights), evaluates deterministic guardrails, runs Human-Owned **Tool Gates** (circuit breakers), and recommends an outcome (`APPROVE`, `REJECT`, or `ESCALATE`).
7. **Human Escalation**: If escalated, the **Human Escalation Service** compiles an executive brief, formats reviewer questionnaires, and synthesizes a spoken `.wav` audio briefing using **Gemini 3.1 Flash Text-to-Speech**.
8. **Independent Audit**: In parallel, the **Gemma Intelligence Layer** performs an out-of-band consistency check to audit the Arbiter's reasoning, providing human-friendly summaries to build absolute operational trust.

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Agent Framework**: Google GenAI SDK (Gemini 2.5 Pro / 3.5 Flash)
- **Audio & TTS Engine**: Gemini 3.1 Flash TTS Preview
- **Verification Engine**: Pydantic V2 (Strict Schema Mapping)
- **Testing Suite**: Pytest (Headless integration testing)

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS & Vanilla HSL CSS variables
- **State Store**: Zustand (Global event subscriber)
- **Transitions**: Framer Motion & Lucide Icons

### Infrastructure & Deployment
- **Deployment target**: Google Cloud Run (Containerized server)
- **Database**: Cloud SQL PostgreSQL & BigQuery
- **Storage**: Cloud Storage (GCS)
- **Containment**: Docker Multi-stage builds & Docker Compose

---

## 📂 Repository Directory Layout

```text
nexusAI/
├── .agents/                    # Customization rules and agent parameters
├── backend/                    # Core Python FastAPI Backend
│   ├── app/
│   │   ├── arbiter/            # Centralized decision engines, aggregators, resolvers
│   │   ├── core/               # Configuration settings, logging, event bus systems
│   │   ├── escalation/         # Human escalation package compilation & TTS audio synthesis
│   │   ├── gemma/              # Out-of-band explanations, decision consistency, and auditer
│   │   ├── models/             # Shared Pydantic data schemas and enums
│   │   ├── workflow/           # Planner orchestration and multi-threaded executors
│   │   ├── gates.py            # Strictly Human-Owned Tool Gate execution blocks
│   │   └── main.py             # Server endpoints, routing, rate limiters, global handlers
│   ├── tests/                  # Complete unit and integration test suite
│   ├── Dockerfile              # Multi-stage production container asset
│   └── pyproject.toml          # Python dependencies & lock manifests
├── frontend/                   # React Next.js Dashboard Frontend
│   ├── src/
│   │   ├── components/         # Premium dashboard layout, widgets, and animation wrappers
│   │   ├── mock/               # Mock scenarios for standalone simulation playbacks
│   │   ├── store/              # Zustand global client-side state store
│   │   └── app/                # Next.js App Router entry pages
│   ├── package.json            # Node dependencies
│   └── FRONTEND.md             # High-level developer frontend document
├── docs/                       # Hackathon-grade system specifications
│   ├── ARCHITECTURE.md         # Extended technical design and GCP topologies
│   ├── DEMO_SCRIPT.md          # Live presentation scripts & playback narratives
│   └── JUDGE_QA.md             # Technical QA guides for DeepMind panels
├── docker-compose.yml          # Container configuration for local deployment
└── README.md                   # Master repository documentation (this file)
```

---

## 🚀 Getting Started

### 📋 Prerequisites
Ensure you have the following installed locally:
- **Docker** & **Docker Compose**
- **Node.js** (v18+)
- **Python** (v3.12)

---

### 🐳 Option A: Unified Local Deployment (Recommended)

To spin up both the FastAPI backend and the Next.js frontend concurrently using Docker Compose:

1. Create a `.env` file in the `backend` directory based on the provided template:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Configure your keys inside `backend/.env`:
   ```env
   GEMINI_API_KEY=your_actual_google_api_key_here
   GOOGLE_API_KEY=your_actual_google_api_key_here
   DEMO_MODE=true # Bypasses cloud service dependencies locally
   ```
3. Run Docker Compose from the root directory:
   ```bash
   docker compose up --build
   ```
4. Access the platforms:
   - **Interactive Frontend**: [http://localhost:3000](http://localhost:3000)
   - **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 💻 Option B: Native Developer Startup

#### 1. Launch the Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e . # Installs project & dependencies using uv
# Or with uv directly: uv pip install -e .

# Launch local server using Uvicorn
PORT=8000 DEMO_MODE=true uvicorn app.main:app --reload
```

#### 2. Launch the Frontend
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) inside your browser.

---

### 🧪 Verifying Systems Health
Run the automated test suites using `pytest` inside the backend directory:
```bash
cd backend
source .venv/bin/activate
DEMO_MODE=true pytest tests/
```

For extended specifications, please refer to the detailed guides inside the [docs/](file:///Users/kiruthick/Developer/nexusAI/docs) directory:
- 🗺️ **Detailed Diagrams & Blueprint Spec**: See [docs/ARCHITECTURE.md](file:///Users/kiruthick/Developer/nexusAI/docs/ARCHITECTURE.md)
- 🎙️ **Demo Flow Scripting Guide**: See [docs/DEMO_SCRIPT.md](file:///Users/kiruthick/Developer/nexusAI/docs/DEMO_SCRIPT.md)
- 🧠 **Technical Judging Q&A Prep**: See [docs/JUDGE_QA.md](file:///Users/kiruthick/Developer/nexusAI/docs/JUDGE_QA.md)
