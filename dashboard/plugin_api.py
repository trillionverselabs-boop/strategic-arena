# Upfront — backend namespace /api/plugins/upfront/
# Mounted by the dashboard plugin loader. Exports a FastAPI APIRouter.
# Desktop reaches these routes via ctx.rest('/...').
#
# The dashboard loader imports this file standalone (not as part of the agent
# plugin package), so we put the plugin root on sys.path and import the engine
# modules by name. The engine + these routes run in the gateway process.

from __future__ import annotations

import json
import sys
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_UPSTREAM = _PLUGIN_ROOT.parent  # the directory that CONTAINS the plugin package
for p in (str(_UPSTREAM), str(_PLUGIN_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from upfront import engine  # noqa: E402
from upfront import portal, reporting  # noqa: E402
from upfront.llm_adapter import LlmAdapter  # noqa: E402
from upfront.models import Intervention  # noqa: E402

router = APIRouter()

_LLM = None


def set_llm(llm) -> None:
    """Bound by the agent plugin's register(ctx) — the only place ctx.llm exists."""
    global _LLM
    _LLM = llm


def _llm():
    if _LLM is None:
        for _name, _mod in list(sys.modules.items()):
            if _mod is None or _mod is sys.modules.get(__name__):
                continue
            if _name.endswith("upfront.dashboard.plugin_api"):
                _bound = getattr(_mod, "_LLM", None)
                if _bound is not None:
                    return _bound
        raise RuntimeError(
            "LLM not bound in backend. The agent plugin half must load and call "
            "plugin_api.set_llm(ctx.llm) in register(); if you only enabled the "
            "dashboard backend, the simulation cannot call the model."
        )
    return _LLM


@router.get("/health")
async def health():
    return {"ok": True, "plugin": "upfront", "llm_ready": _LLM is not None}


@router.post("/run")
async def run(body: dict):
    """Start a review in a background thread. Returns {run_id} immediately."""
    try:
        scenario = _scenario_from(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid scenario: {exc}")

    run_id = uuid.uuid4().hex[:12]
    engine._emit(run_id, "running", 0, scenario.rounds)

    def _work():
        try:
            def _on_round(snap):
                engine._emit(run_id, "running", snap.round, scenario.rounds,
                             {k: round(v, 3) for k, v in (snap.stances or {}).items()})
            base = _llm()
            chosen = (scenario.model or "").strip()
            llm = base
            if chosen and chosen != "default":
                llm = LlmAdapter(
                    base._llm, temperature=scenario.temperature, model=chosen,
                    allow_override=getattr(base, "allow_override", False),
                )
            result = engine.run_scenario_progress(
                scenario, llm, on_round=_on_round, run_id=run_id
            )
            engine._emit(run_id, "done", result.rounds, result.rounds,
                         {p.name: round(p.stance, 3) for p in result.personas})
        except Exception as exc:
            engine._emit(run_id, "failed", 0, scenario.rounds)
            with engine._LOCK:
                engine._PROGRESS[run_id]["error"] = str(exc)

    threading.Thread(target=_work, daemon=True).start()
    return {"run_id": run_id, "status": "running"}


@router.get("/status/{run_id}")
async def status(run_id: str):
    prog = dict(engine.get_progress(run_id))
    try:
        meta = json.loads((reporting.runs_dir() / run_id / "meta.json").read_text())
        prog["sea"] = {
            "state": meta.get("sea_state", ""), "label": meta.get("sea_label", ""),
            "color": meta.get("sea_color", ""), "level": meta.get("sea_level", ""),
            "why": meta.get("sea_why", ""),
        }
        prog["claims"] = meta.get("claims", 0)
        prog["degraded"] = meta.get("degraded", False)
    except Exception:
        pass
    return prog


@router.post("/inject/{run_id}")
async def inject(run_id: str, body: dict):
    description = str(body.get("description", "")).strip()
    if not description:
        raise HTTPException(status_code=400, detail="description required")
    iv = Intervention(
        name=str(body.get("name", "Counter-move")),
        description=description,
        inject_at_round=1,  # queue position wins; the round field is informational
    )
    ok = engine.inject(run_id, iv)
    return {"queued": ok, "run_id": run_id}


@router.get("/graph/{run_id}")
async def graph(run_id: str):
    data = reporting.load_run(run_id)
    if data.get("graph"):
        return data["graph"]
    from upfront.graph import GraphStore
    from upfront.paths import graph_path
    return GraphStore(graph_path()).as_payload()


@router.get("/report/{run_id}")
async def report(run_id: str, full: bool = False):
    data = reporting.load_run(run_id)
    key = "report_full" if full else "report"
    if not data.get(key):
        raise HTTPException(status_code=404, detail="run not found or not finished")
    return {"report": data[key], "full": full}


@router.get("/claims/{run_id}")
async def claims(run_id: str):
    return {"claims": reporting.load_claims(run_id)}


@router.post("/verify/{run_id}")
async def verify(run_id: str, body: dict):
    try:
        return reporting.mark_verified(
            run_id,
            str(body.get("verdict", "")),
            str(body.get("note", "")),
            hits=body.get("hits") or {},
            actual_friction=body.get("actual_friction"),
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="run not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/calibration")
async def calibration():
    return reporting.calibration()


@router.get("/models")
async def models(free: bool = False):
    """Live Nous model catalogue with per-million-token prices (public, no creds)."""
    cat = portal.catalogue()
    items = cat.get("models", [])
    if free:
        items = [m for m in items if m.get("free")]
    return {
        "models": items,
        "count": len(items),
        "free_count": cat.get("free_count", 0),
        "fetched_at": cat.get("fetched_at", ""),
        "source": cat.get("source", ""),
        "error": cat.get("error", ""),
    }


@router.get("/compare")
async def compare(title: str = "", limit: int = 20):
    """Same decision across timelines: friction spread, veto-player stability, drift."""
    return reporting.compare_runs(title, limit)


@router.get("/history")
async def history(limit: int = 20):
    return reporting.list_runs(limit)


# ── helpers ──────────────────────────────────────────────────────────

def _scenario_from(body: dict):
    from upfront.models import Document, Persona, Scenario

    docs = [Document(**d) for d in body.get("documents", []) if d.get("content")]
    personas = [Persona(**p) for p in body.get("personas", [])]
    interventions = [Intervention(**iv) for iv in body.get("interventions", [])]
    return Scenario(
        title=body.get("title", "Untitled"),
        goal=body.get("goal", "adoption"),
        documents=docs,
        urls=body.get("urls", []) or [],
        window=body.get("window", "24h"),
        model=body.get("model", "default"),
        personas=personas,
        interventions=interventions,
        max_personas=body.get("max_personas", 8),
        temperature=body.get("temperature", 0.6),
    )
