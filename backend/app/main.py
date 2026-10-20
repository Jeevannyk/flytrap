"""FastAPI app: run scenarios, inspect sessions, investigate, verify, reset."""
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .chain import Store
from .config import setting
from .evaluate import evaluate
from .llm_agent import LLMError
from .replay import investigate
from .runner import AGENTS, run_scenario
from .scenarios import SCENARIOS

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

app = FastAPI(title="FLYTRAP")
store = Store(setting("FLYTRAP_DB", ":memory:"))
LIVE = {}  # session_id -> Gateway (lives in memory; resets need it)


class RunBody(BaseModel):
    scenario: str
    protected: bool = True
    agent: str = "sim"


def _detail(session_id):
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(404, "unknown session")
    return {"session": session, "events": store.events(session_id), "chain": store.verify(session_id)}


@app.get("/api/scenarios")
def scenarios():
    return [{"id": s.id, "title": s.title, "expectation": s.expectation} for s in SCENARIOS.values()]


@app.post("/api/run")
def run(body: RunBody):
    if body.scenario not in SCENARIOS:
        raise HTTPException(400, "unknown scenario")
    if body.agent not in AGENTS:
        raise HTTPException(400, "unknown agent")
    try:
        session_id, gw, _, _ = run_scenario(store, body.scenario, body.protected, agent=body.agent)
    except LLMError as e:
        raise HTTPException(502, f"Live LLM failed: {e}")
    LIVE[session_id] = gw
    return _detail(session_id)


@app.get("/api/sessions")
def sessions():
    return store.list_sessions()


@app.get("/api/sessions/{session_id}")
def session(session_id: str):
    return _detail(session_id)


@app.post("/api/sessions/{session_id}/investigate")
def investigate_session(session_id: str):
    _detail(session_id)
    try:
        return investigate(store, session_id)
    except LLMError as e:
        raise HTTPException(502, f"Live LLM failed during replay: {e}")


@app.post("/api/sessions/{session_id}/reset")
def reset(session_id: str, x_admin_key: str = Header(default="")):
    if x_admin_key != setting("FLYTRAP_ADMIN_KEY", "demo-admin"):
        raise HTTPException(403, "authorized reset required")
    gw = LIVE.get(session_id)
    if not gw:
        raise HTTPException(404, "session not live")
    gw.reset()
    return _detail(session_id)


@app.post("/api/sessions/{session_id}/tamper")
def tamper(session_id: str):
    """Demo only: edit a stored record to show the hash chain detecting it."""
    _detail(session_id)
    store.tamper(session_id, 1)
    return _detail(session_id)


@app.get("/api/evaluate")
def evaluation():
    return evaluate()


# Serve the built React app. Registered last so /api routes take precedence.
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    @app.get("/")
    def frontend_missing():
        return PlainTextResponse("Frontend not built. Run: cd frontend && npm install && npm run build")
