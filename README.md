AI Search Agent
================

[![CI Pipeline](https://github.com/shivsharma-ss/ai-search-agent/workflows/CI%20Pipeline/badge.svg)](https://github.com/shivsharma-ss/ai-search-agent/actions)

Multi‑source research agent that queries Google, Bing, and Reddit, summarizes each source with an LLM, and synthesizes a final answer. Built with a production‑minded stack and clear separation between a FastAPI backend and a Vite/React frontend.

Highlights
- FastAPI backend with a LangGraph‑based pipeline and clear API surface
- Vite/React/Tailwind frontend with a polished UI and fun loading animations
- Bright Data integration for SERP + Reddit (posts search and comments by URL)
- Preflight checks for keys/tokens with helpful CLI logs
- Tests for pipeline and API behavior (pytest)

Quick Start
- Requirements
  - Python 3.11+
  - Node.js 18+

- Environment
  - Copy `.env.example` to `.env` and fill in values:
    - `OPENAI_API_KEY`
    - `BRIGHTDATA_API_KEY`
    - Optional: `REDDIT_DATASET_ID`, `REDDIT_COMMENTS_DATASET_ID` (you can also set these in the UI)
  - The repo is configured to ignore secrets (`.env` is in `.gitignore`). The included `.env` now contains placeholders only.

- Install (backend)
  - With uv: `uv sync`
  - Or pip: `pip install -e .`

- Run backend
  - `uvicorn ai_search_agent.api:app --reload --port 8000`
  - Docs at http://localhost:8000/docs

- Run frontend
  - `cd frontend && npm install && npm run dev`
  - Open http://localhost:5173
  - Use the Settings dialog to enter keys/tokens and dataset IDs, then “Test Settings”. You may also “Save to server” for the current session.

- Run tests
  - `pytest`

## 🚀 CI/CD Pipeline

This project includes a comprehensive GitHub Actions CI/CD pipeline that runs on every push and pull request:

### **Automated Testing:**
- ✅ **Backend Tests**: Runs pytest with coverage
- ✅ **Frontend Tests**: Builds and validates React app
- ✅ **Code Quality**: Black formatting, flake8 linting
- ✅ **Integration Tests**: Tests backend startup and frontend build

### **Quality Gates:**
- All tests must pass before merging
- Code formatting is automatically checked
- Security vulnerabilities are scanned
- Build artifacts are preserved for 7 days

### **Future Deployment:**
- Staging deployment on `develop` branch
- Production deployment on `main` branch
- Environment-specific configurations
- Automated rollbacks on failure

**View the pipeline:** [GitHub Actions](https://github.com/shivsharma-ss/ai-search-agent/actions)

## Architecture
- `ai_search_agent/pipeline.py`: LangGraph pipeline orchestrating:
  - SERP via Bright Data (Google/Bing)
  - Reddit posts search (dataset) → select URLs → Reddit comments retrieval (dataset)
  - LLM analyses per source → synthesis into final answer
  - Clear CLI logs marking each step
- `ai_search_agent/api.py`: FastAPI app exposing:
  - `GET /health`
  - `GET/POST /api/settings` for ephemeral session storage
  - `POST /api/test-settings` for consolidated preflight
  - `POST /api/research` running the pipeline (with preflight)
  - `GET /api/runs` and simple share endpoints backed by SQLite
- `ai_search_agent/web_operations.py`: Bright Data SERP + dataset trigger/snapshot utilities
- `ai_search_agent/snapshot_operations.py`: polling + downloading with clear progress logs
- `frontend/`: Vite/React/Tailwind UI with neon card, starfield bg, ripple buttons, and quirky loading panel

Operational Notes
- Keys fall back to environment variables on the server if not supplied by the UI.
- Preflight is run before each research call and will return a 400 with a concise reason if something is misconfigured.
- The `/api/research` response is sanitized to only JSON‑safe fields so logs and DB storage never choke on non‑serializable objects.

API Surface (short)
- `POST /api/research` body:
  - `{ question, openai_api_key?, brightdata_api_key?, reddit_dataset_id?, reddit_comments_dataset_id? }`
- `POST /api/test-settings` body:
  - `{ openai_api_key?, brightdata_api_key?, reddit_dataset_id?, reddit_comments_dataset_id? }`
- See `http://localhost:8000/docs` for full schemas.

Project Structure
- `ai_search_agent/` – backend package (API, pipeline, ops)
- `frontend/` – React UI
- `tests/` – pytest unit and API tests
- `.env.example` – safe template for environment variables
- `pyproject.toml` – package + CLI entry (`ai-search-agent`)

Security & Secrets
- `.env` is git‑ignored. The committed `.env` contains placeholders only.
- Do not commit real keys. Use `.env` locally and environment variables in CI/hosting.

Bright Data Datasets
- This project expects dataset IDs (start with `gd_…`) for:
  - Reddit – Posts (discover/collect)
  - Reddit – Comments (collect by URL)
- You can set these in the Settings dialog or via env vars.

Finishing Touches (done)
- Loading panel with humorous status updates while the backend processes
- Click‑through fixes for overlays and consistent input theming for better contrast
- Preflight checks with helpful console logs
- API result sanitization to ensure JSON‑safe responses and DB storage
- Additional tests for API endpoints, preflight, and sanitization
- Safer defaults: `.env.example`, `.gitignore` expanded, and secrets removed

Roadmap / Future Upgrades
- Docker & Compose: containerize backend and frontend, add health checks and a dev compose file (with volume for DB and optional Redis).
- Chat continuity: persistent conversation state per session (e.g., Redis + session keys) and UI chat log.
- More sources: YouTube transcripts, arXiv/semantic scholar, StackOverflow, Hacker News, Product Hunt.
- MCP support: integrate Model Context Protocol tools for richer retrieval/actions.
- Observability: OpenTelemetry tracing, structured logs, and a minimal /metrics endpoint.
- Caching: Redis for SERP/dataset caching + ETag/If‑None‑Match handling to reduce cost and latency.
- Rate limiting/backoff: polite exponential backoff and concurrency guards around external APIs.
- Background jobs: move slow dataset triggers to a queue (RQ/Celery) with callbacks to stream progress to the UI.
- Configurable models: pick model per source, temperature, and token budgets via Settings.
- Security hardening: origin‑restricted CORS, cookie security flags, signed run IDs, and optional OAuth SSO.

Why This Project
- Demonstrates a clean separation of concerns, approachable code paths, pragmatic logging, and a polished UI—ready to extend into a production app or demo on your portfolio.

License
- MIT (add or change as you prefer).
