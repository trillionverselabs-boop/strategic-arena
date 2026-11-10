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
from upfront import llm_binding, portal, reporting  # noqa: E402
from upfront.llm_adapter import LlmAdapter  # noqa: E402
from upfront.models import Intervention  # noqa: E402

import os  # noqa: E402
import time  # noqa: E402

router = APIRouter()


def _debug(msg: str) -> None:
    """One line per model resolution, in the profile's data dir (survives updates).

    Cheap, and it turns "Run failed" into a diagnosis: whether the agent half was
    bound in *this* process, or whether we fell back to the local provider config.
    """
    try:
        from upfront import paths

        path = paths.data_root() / "desktop-debug.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} pid={os.getpid()} {msg}\n")
    except Exception:
        pass


def set_llm(llm) -> None:
    """Bound by the agent plugin's register(ctx) — kept for compatibility.

    The binding itself lives in `upfront.llm_binding` (a process-wide holder)
    because this file is imported standalone from its path, under a different
    module name than the agent half: module globals here are not shared with it.
    """
    llm_binding.set_llm(llm)


def _resolve_llm():
    """(adapter, source) — the host binding if this process has it, else the floor.

    The holder only works when `register(ctx)` ran in the same process as these
    routes. In the desktop deployment it may not have, and no in-process trick
    crosses a process boundary — so fall back to building the model from the
    credentials this machine already has. Never leave the user staring at
    "LLM not bound" when a run is perfectly possible.
    """
    bound = llm_binding.get_llm()
    if bound is not None:
        return bound, "agent"

    # A copy of this module imported under another name may hold an old binding.
    for _name, _mod in list(sys.modules.items()):
        if _mod is None or _mod is sys.modules.get(__name__):
            continue
        if _name.endswith("upfront.dashboard.plugin_api"):
            _bound = getattr(_mod, "_LLM", None)
            if _bound is not None:
                return _bound, "agent-copy"

    try:
        from upfront.host_llm import build_host_llm

        built = LlmAdapter(build_host_llm(), allow_override=True)
        _debug("model source=host-facade (agent half not bound in this process)")
        return built, "host-config"
    except Exception as exc:
        _debug(f"model source=none ({exc})")
        raise RuntimeError(
            "No model available. The agent plugin half is not loaded in this process "
            f"and the local provider credentials could not be used: {exc}"
        )


def _llm():
    return _resolve_llm()[0]


@router.get("/health")
async def health():
    try:
        _, source = _resolve_llm()
    except Exception as exc:
        return {"ok": False, "plugin": "upfront", "llm_ready": False, "detail": str(exc)}
    return {"ok": True, "plugin": "upfront", "llm_ready": True, "source": source}


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
            # if the host refused the chosen model, say so once, next to the run
            note = getattr(getattr(base, "_llm", None), "override_denied_note", "") or ""
            if note:
                try:
                    (reporting.runs_dir() / run_id / "model-note.txt").write_text(note)
                except Exception:
                    pass
            engine._emit(run_id, "done", result.rounds, result.rounds,
                         {p.name: round(p.stance, 3) for p in result.personas})
        except engine.SimulationCancelled:
            engine._emit(run_id, "cancelled", 0, scenario.rounds)
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


@router.post("/cancel/{run_id}")
async def cancel(run_id: str):
    """Stop a live run at the next round boundary. Nothing partial is saved."""
    return {"ok": engine.cancel(run_id), "run_id": run_id}


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
    # The summary card reads these without parsing the markdown; the page leads
    # with them, the audit is behind an expander.
    meta = {}
    try:
        meta = json.loads((reporting.runs_dir() / run_id / "meta.json").read_text())
    except Exception:
        pass
    model_note = ""
    try:
        model_note = (reporting.runs_dir() / run_id / "model-note.txt").read_text().strip()
    except Exception:
        pass
    return {
        "report": data[key], "full": full, "model_note": model_note,
        "recommendation": meta.get("recommendation") or "",
        "summary": meta.get("summary") or "",
        "blocker": meta.get("blocker"),
        "blocker_stance": meta.get("blocker_stance"),
        "blocker_capacity": meta.get("blocker_capacity"),
        "counter_moves": meta.get("counter_moves") or [],
        "personas": meta.get("personas") or [],
        "interventions": meta.get("interventions") or [],
        "camps": meta.get("camps") or [],
    }


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


@router.get("/model-access")
async def model_access():
    """Whether the host will honour a model chosen in the picker.

    Reads exactly what the enforcer reads (`PluginLlm` → `plugins.entries.<id>.llm`),
    so the form can warn before a run instead of the user discovering it after.
    Never returns credentials — this is a boolean about a permission.
    """
    allowed = False
    allowed_models: list[str] = []
    try:
        from hermes_cli.config import load_config_readonly

        plugins_cfg = (load_config_readonly() or {}).get("plugins") or {}
        entry = ((plugins_cfg.get("entries") or {}).get("upfront") or {})
        llm_cfg = entry.get("llm") or {}
        allowed = bool(llm_cfg.get("allow_model_override"))
        raw = llm_cfg.get("allowed_models")
        if isinstance(raw, (list, tuple)):
            allowed_models = [str(x) for x in raw]
    except Exception:
        pass
    return {"allowed": allowed, "allowed_models": allowed_models,
            "config_key": "plugins.entries.upfront.llm.allow_model_override"}


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


@router.get("/due")
async def due():
    """Runs whose window has closed and that are still unscored.

    The desktop and `upfront_due` both read this — one payload, one truth.
    """
    rows = reporting.due_claims()
    return {"due": rows, "count": len(rows)}


@router.get("/export/{run_id}")
async def export(run_id: str, out_dir: str = "decisions"):
    """Write the decision record to disk and return its path + markdown."""
    try:
        path = reporting.export_decision(run_id, out_dir=out_dir)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="run not found")
    text = ""
    try:
        with open(path) as fh:
            text = fh.read()
    except OSError:
        pass
    return {"run_id": run_id, "path": path, "markdown": text}



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
