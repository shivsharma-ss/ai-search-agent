"""FastAPI application exposing the research pipeline as REST API.

Endpoints:
- GET /health: Simple health check
- POST /api/research: Run research pipeline for a given question
"""

import os
import uuid
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .db import clear_runs as db_clear_runs
from .db import create_share as db_create_share
from .db import get_run as db_get_run
from .db import get_shared as db_get_shared
from .db import init_db
from .db import list_runs as db_list_runs
from .db import save_run as db_save_run
from .pipeline import run_research
from .preflight import preflight_check

load_dotenv()
init_db()

app = FastAPI(title="AI Search Agent", version="0.1.0")

# Enable CORS for local dev; adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    question: str = Field(..., description="User question to research")
    openai_api_key: str | None = Field(None, description="OpenAI API key")
    brightdata_api_key: str | None = Field(None, description="Bright Data API key")
    reddit_dataset_id: str | None = Field(
        None, description="Bright Data dataset id for Reddit search"
    )
    reddit_comments_dataset_id: str | None = Field(
        None, description="Bright Data dataset id for Reddit comments"
    )


class ResearchResponse(BaseModel):
    final_answer: Optional[str]
    google_results: Optional[Dict[str, Any]] = None
    bing_results: Optional[Dict[str, Any]] = None
    reddit_results: Optional[Dict[str, Any]] = None
    reddit_post_data: Optional[Dict[str, Any]] = None
    google_analysis: Optional[str] = None
    bing_analysis: Optional[str] = None
    reddit_analysis: Optional[str] = None


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/research", response_model=ResearchResponse)
def research(payload: ResearchRequest, request: Request):
    try:
        # Merge session-stored settings with request payload
        # Priority: payload value > session-stored value > None
        session_id = _get_session_id(request)
        session_settings = SETTINGS_STORE.get(session_id, {})

        openai_api_key = (
            payload.openai_api_key
            or session_settings.get("openai_api_key")
            or os.getenv("OPENAI_API_KEY")
        )
        bda_key = (
            payload.brightdata_api_key
            or session_settings.get("brightdata_api_key")
            or os.getenv("BRIGHTDATA_API_KEY")
        )
        reddit_ds = payload.reddit_dataset_id or session_settings.get(
            "reddit_dataset_id"
        )
        reddit_comments_ds = payload.reddit_comments_dataset_id or session_settings.get(
            "reddit_comments_dataset_id"
        )

        config = {
            "brightdata_api_key": bda_key,
            "reddit_dataset_id": reddit_ds,
            "reddit_comments_dataset_id": reddit_comments_ds,
        }
        # Preflight checks before starting actual research
        print("\n🔍 Received research request. Running preflight checks…")
        pf = preflight_check(
            openai_api_key=openai_api_key,
            brightdata_api_key=bda_key,
            reddit_dataset_id=reddit_ds,
            reddit_comments_dataset_id=reddit_comments_ds,
        )
        if not pf.get("ok"):
            # Summarize failures
            parts = []
            for k in (
                "openai",
                "brightdata_api",
                "reddit_dataset",
                "reddit_comments_dataset",
            ):
                r = pf.get(k) or {}
                if not r.get("ok"):
                    parts.append(f"{k}: {r.get('message')}")
            msg = "; ".join(parts) or "Preflight failed"
            print(f"🚫 Aborting research due to preflight failure: {msg}")
            raise HTTPException(status_code=400, detail=f"Preflight failed: {msg}")

        print("🚀 Preflight passed. Starting research pipeline…")
        result = run_research(
            payload.question, config=config, openai_api_key=openai_api_key
        )

        # Sanitize pipeline output: keep only fields defined in the
        # response model and ensure values are JSON-serializable.
        safe_response = ResearchResponse(**result)
        safe_payload = safe_response.model_dump(exclude_none=True)

        run_id = uuid.uuid4().hex
        db_save_run(session_id, run_id, payload.question, safe_payload)

        return safe_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Server-side session storage (in-memory) ---
SESSION_COOKIE = "ASA_SESSION"
SETTINGS_STORE: Dict[str, Dict[str, Optional[str]]] = {}
# Past research runs are persisted in SQLite (see db.py)


@app.middleware("http")
async def attach_session(request: Request, call_next):
    # Ensure a session cookie exists; attach session id to request state
    session_id = request.cookies.get(SESSION_COOKIE)
    new_session = False
    if not session_id:
        session_id = uuid.uuid4().hex
        new_session = True
    request.state.session_id = session_id

    # If the request body is JSON we want to attach session_id to the parsed payload later
    response: Response = await call_next(request)
    if new_session:
        response.set_cookie(
            SESSION_COOKIE,
            session_id,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=60 * 60 * 24 * 7,
        )
    return response


def _get_session_id(request: Request) -> str:
    sid = getattr(request.state, "session_id", None)
    if not sid:
        raise HTTPException(status_code=400, detail="Missing session")
    return sid


class SettingsPayload(BaseModel):
    openai_api_key: Optional[str] = None
    brightdata_api_key: Optional[str] = None
    reddit_dataset_id: Optional[str] = None
    reddit_comments_dataset_id: Optional[str] = None


class SettingsMeta(BaseModel):
    has_openai_api_key: bool
    has_brightdata_api_key: bool
    reddit_dataset_id: Optional[str] = None
    reddit_comments_dataset_id: Optional[str] = None


@app.get("/api/settings", response_model=SettingsMeta)
def get_settings(request: Request):
    sid = _get_session_id(request)
    cur = SETTINGS_STORE.get(sid, {})
    return SettingsMeta(
        has_openai_api_key=bool(cur.get("openai_api_key")),
        has_brightdata_api_key=bool(cur.get("brightdata_api_key")),
        reddit_dataset_id=cur.get("reddit_dataset_id"),
        reddit_comments_dataset_id=cur.get("reddit_comments_dataset_id"),
    )


@app.post("/api/settings", response_model=SettingsMeta)
def save_settings(payload: SettingsPayload, request: Request):
    sid = _get_session_id(request)
    cur = SETTINGS_STORE.setdefault(sid, {})
    # Update only provided values
    for key, value in payload.model_dump().items():
        if value is not None:
            cur[key] = value
    return get_settings(request)


class TestSettingsResponse(BaseModel):
    ok: bool
    brightdata_ok: bool
    openai_ok: Optional[bool] = None
    reddit_dataset_ok: Optional[bool] = None
    reddit_comments_dataset_ok: Optional[bool] = None
    message: Optional[str] = None


@app.post("/api/test-settings", response_model=TestSettingsResponse)
def test_settings(payload: SettingsPayload, request: Request):
    # Run consolidated preflight using saved + provided settings
    sid = _get_session_id(request)
    cur = SETTINGS_STORE.get(sid, {})
    bright = (
        payload.brightdata_api_key
        or cur.get("brightdata_api_key")
        or os.getenv("BRIGHTDATA_API_KEY")
    )
    openai_key = (
        payload.openai_api_key
        or cur.get("openai_api_key")
        or os.getenv("OPENAI_API_KEY")
    )
    reddit_ds = payload.reddit_dataset_id or cur.get("reddit_dataset_id")
    reddit_comments_ds = payload.reddit_comments_dataset_id or cur.get(
        "reddit_comments_dataset_id"
    )

    pf = preflight_check(
        openai_api_key=openai_key,
        brightdata_api_key=bright,
        reddit_dataset_id=reddit_ds,
        reddit_comments_dataset_id=reddit_comments_ds,
    )
    return TestSettingsResponse(
        ok=bool(pf.get("ok")),
        brightdata_ok=bool((pf.get("brightdata_api") or {}).get("ok")),
        openai_ok=bool((pf.get("openai") or {}).get("ok")),
        reddit_dataset_ok=bool((pf.get("reddit_dataset") or {}).get("ok")),
        reddit_comments_dataset_ok=bool(
            (pf.get("reddit_comments_dataset") or {}).get("ok")
        ),
        message=(
            None
            if pf.get("ok")
            else "; ".join(
                [
                    (
                        f"openai: {(pf.get('openai') or {}).get('message')}"
                        if not (pf.get("openai") or {}).get("ok")
                        else None
                    ),
                    (
                        f"brightdata: {(pf.get('brightdata_api') or {}).get('message')}"
                        if not (pf.get("brightdata_api") or {}).get("ok")
                        else None
                    ),
                    (
                        f"reddit_dataset: {(pf.get('reddit_dataset') or {}).get('message')}"
                        if not (pf.get("reddit_dataset") or {}).get("ok")
                        else None
                    ),
                    (
                        f"reddit_comments_dataset: {(pf.get('reddit_comments_dataset') or {}).get('message')}"
                        if not (pf.get("reddit_comments_dataset") or {}).get("ok")
                        else None
                    ),
                ]
            )
            .strip("; ")
            .replace("None; ", "")
            .replace("; None", "")
        ),
    )


class RunMeta(BaseModel):
    id: str
    ts: int
    question: str
    has_answer: bool


@app.get("/api/runs", response_model=List[RunMeta])
def list_runs(request: Request):
    sid = _get_session_id(request)
    return db_list_runs(sid)


@app.get("/api/runs/{run_id}")
def get_run(run_id: str, request: Request):
    sid = _get_session_id(request)
    r = db_get_run(sid, run_id)
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
    return r


@app.delete("/api/runs")
def clear_runs(request: Request):
    sid = _get_session_id(request)
    db_clear_runs(sid)
    return {"ok": True}


class ShareResponse(BaseModel):
    share_id: str
    url: str


@app.post("/api/runs/{run_id}/share", response_model=ShareResponse)
def share_run(run_id: str, request: Request):
    sid = _get_session_id(request)
    r = db_get_run(sid, run_id)
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
    share_id = uuid.uuid4().hex
    db_create_share(run_id, share_id)
    base = str(request.base_url).rstrip("/")
    return ShareResponse(share_id=share_id, url=f"{base}/api/share/{share_id}")


@app.get("/api/share/{share_id}")
def get_shared_run(share_id: str):
    r = db_get_shared(share_id)
    if not r:
        raise HTTPException(status_code=404, detail="Shared run not found")
    return r
