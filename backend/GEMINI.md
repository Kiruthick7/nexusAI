# 🤖 Nexus AI Operations Platform - Development Guidelines & Rules

Welcome to the development handbook for the Nexus AI Operations Platform backend. This document establishes core architectural boundaries, coding standards, environment policies, and security constraints to keep our system clean, modular, and production-ready.

---

## 📂 1. Project Directory Structure

Our project isolates the Next.js frontend from our event-driven Python FastAPI backend. The backend structure is organized as follows:

```
backend/
├── .env.example              # Template configuration variables
├── pyproject.toml            # Project description and package requirements (uv)
├── server.py                 # Main entrypoint runner for local uvicorn execution
├── GEMINI.md                 # Dev guidelines, security rules, and boundaries
├── app/                      # Main application module
│   ├── __init__.py
│   ├── main.py               # Minimal FastAPI app instantiation and route roots
│   ├── gates.py              # [HUMAN OWNED] Tool Gates and Security Guardrails
│   ├── api/                  # API routers, routes, endpoints
│   ├── agents/               # Autonomous LLM Orchestration agent logic
│   ├── tools/                # Declarative tool definitions invoked by agents
│   ├── services/             # Specialized services (BigQuery, OCR integrations)
│   ├── schemas/              # Pydantic serializer request/response schemas
│   ├── models/               # Pure domain models (Claim, Event, Mission)
│   ├── providers/            # Third-party integrations (Gemini API, GCP APIs)
│   └── core/                 # Central platform utilities
│       ├── config.py         # Config loader singleton using Pydantic Settings
│       ├── logger.py         # Structured JSON logging configurations
│       └── dependencies.py   # Dependency injection container
├── shared/
│   └── events.md             # SSE Event Contract Single Source of Truth
├── scripts/                  # Command line automation utilities and setup scripts
└── tests/                    # Unit, integration, and end-to-end test suites
```

---

## 🔒 2. Human-Owned Files Boundary

To preserve platform security, select files are designated as **HUMAN OWNED**.
- **🚨 Core Security Guardrail**: `backend/app/gates.py` is strictly human owned.
- **Rule**: AI agents, automated copilots, and automatic refactoring tools are **STRICTLY PROHIBITED** from editing, deleting, or overwriting `backend/app/gates.py` without human supervision. All changes here must be completed manually.

---

## 🐍 3. Coding Standards

Every developer (human or AI) must conform to these standards:
- **Type Hints**: Type annotations are **mandatory** on all function signatures, parameters, and variable assignments. Avoid `Any` wherever possible.
- **Documentation**:
  - Every Python module (file) **must begin with a docstring** (`"""..."""`) summarizing its architecture role.
  - Every class and function must contain a descriptive docstring defining inputs, outputs, and potential raises (Google Docstring Format is preferred).
- **Error Handling**: Use explicit try-except catch blocks with context logging. Avoid blank or silent catches (`except: pass` is prohibited).
- **Central Settings**: Never hardcode ports, keys, or endpoints. Always load values through the central config settings instance:
  ```python
  from app.core.config import settings
  ```

---

## ⚙️ 4. Environment Variables Policy

- **Templating**: All required configuration variables must exist in `.env.example` with empty values. Never commit actual secret keys or active database strings.
- **Naming Conventions**: Use `UPPER_SNAKE_CASE` for environment configuration parameters (e.g., `NEON_DATABASE_URL`).
- **Pydantic Validation**: All configurations must be mapped to `app/core/config.py` with validated type wrappers (e.g. `PORT: int = 8000`).

---

## 🧠 5. Agent & Tool Boundaries

- **Separation of Concerns**: Agents (`app/agents/`) must never contain raw tool execution code. Instead, tools must be declared separately as modules in `app/tools/` and resolved via schemas.
- **Event-Driven Communication**: Agents do not directly push payloads to the client. They write checkpoint event structures to the streaming pipeline, matching the contracts defined in `shared/events.md`.
- **Tool Gates**: Any critical service execution (e.g., database writes, cloud storage uploads, third-party requests) must go through the evaluation gates in `app/gates.py` before execution.

---

## 🚀 6. Deployment Notes

- **Package Management**: We use `uv` for lightning-fast, reproducible dependency resolutions. Use `uv add <pkg>` instead of raw pip.
- **Process Manager**: The application boots locally via Uvicorn. In staging and production, always run behind a proper ASGI process controller (e.g., Gunicorn with Uvicorn workers) under Docker containers.
