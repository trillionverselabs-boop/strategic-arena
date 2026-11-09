# Upfront Prediction — backend namespace /api/plugins/upfront/
# Mounted by the dashboard plugin loader. Exports a FastAPI APIRouter.
# Desktop reaches these routes via ctx.rest('/...').
#
# The dashboard loader imports this file standalone (not as part of the agent
# plugin package), so we put the plugin root on sys.path and import the engine
# modules by name. The engine + these routes run in the gateway process.

from __future__ import annotations

import sys
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_UPSTREAM = _PLUGIN_ROOT.parent  # the directory that CONTAINS the upfront package
for p in (str(_UPSTREAM), str(_PLUGIN_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from upfront import engine  # noqa: E402
from upfront import reporting  # noqa: E402
from upfront.models import Document, Intervention, Persona, Scenario  # noqa: E402

router = APIRouter()

_LLM = None


def set_llm(llm) -> None:
    """Bound by the agent plugin's register(ctx) — the only place ctx.llm exists."""
    global _LLM
    _LLM = llm


def _llm():
    if _LLM is None:
        raise RuntimeError(
            "LLM not bound in backend. The agent plugin half must load and call "
            "plugin_api.set_llm(ctx.llm) in register(); if you only enabled the "
            "dashboard backend, the simulation cannot call the model."
        )
    return _LLM


@router.get("/health")
async def health():
    llm_ready = _LLM is not None
    return {"ok": True, "plugin": "upfront", "llm_ready": llm_ready}


@router.post("/run")
async def run(body: dict):
    """Start a simulation in a background thread. Returns {run_id} immediately."""
    try:
        scenario = _scenario_from(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid scenario: {exc}")

    run_id = uuid.uuid4().hex[:12]
    engine._emit(run_id, "running", 0, scenario.rounds)

    def _work():
        try:
            result = engine.run_scenario_progress(scenario, _llm())
            # engine mints its own run_id on completion; re-key progress under ours
            engine._emit(run_id, "done", result.rounds, result.rounds,
                         {p.name: round(p.stance, 3) for p in result.personas})
            # tag the persisted run so the desktop can load it by our id
            (Path.home() / ".hermes" / "upfront" / "runs" / run_id).mkdir(parents=True, exist_ok=True)
            import json
            (Path.home() / ".hermes" / "upfront" / "runs" / run_id / "meta.json").write_text(json.dumps({
                "run_id": run_id, "title": result.title, "goal": result.goal.value,
                "created_at": result.created_at, "friction": result.friction,
                "blocker": result.blocker.name if result.blocker else None,
                "summary": result.summary, "engine_run_id": result.run_id,
            }, indent=1))
        except Exception as exc:  # pragma: no cover - surfaced via /status
            engine._emit(run_id, "failed", 0, scenario.rounds)
            engine._PROGRESS[run_id]["error"] = str(exc)

    t = threading.Thread(target=_work, daemon=True)
    t.start()
    return {"run_id": run_id, "status": "running"}


@router.get("/status/{run_id}")
async def status(run_id: str):
    return engine.get_progress(run_id)


@router.get("/graph/{run_id}")
async def graph(run_id: str):
    data = reporting.load_run(run_id)
    if data.get("graph"):
        return data["graph"]
    from upfront.graph import GraphStore
    return GraphStore(engine.GRAPH_PATH).as_payload()


@router.get("/report/{run_id}")
async def report(run_id: str, full: bool = False):
    data = reporting.load_run(run_id)
    key = "report_full" if full else "report"
    if not data.get(key):
        raise HTTPException(status_code=404, detail="run not found or not finished")
    return {"report": data[key], "full": full}


@router.get("/history")
async def history(limit: int = 20):
    return reporting.list_runs(limit)


# ── helpers ──────────────────────────────────────────────────────────

def _scenario_from(body: dict) -> Scenario:
    docs = [Document(**d) for d in body.get("documents", [])]
    personas = [Persona(**p) for p in body.get("personas", [])]
    interventions = [Intervention(**iv) for iv in body.get("interventions", [])]
    return Scenario(
        title=body.get("title", "Untitled"),
        goal=body.get("goal", "adoption"),
        documents=docs,
        window=body.get("window", "24h"),
        model=body.get("model", "default"),
        personas=personas,
        interventions=interventions,
        max_personas=body.get("max_personas", 8),
        temperature=body.get("temperature", 0.6),
    )
