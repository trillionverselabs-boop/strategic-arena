# Strategic Arena — backend namespace /api/plugins/strategic-arena/
# Mounted by the dashboard plugin loader. Exports a FastAPI APIRouter.
# Desktop reaches these routes via ctx.rest('/...').
#
# The dashboard loader imports this file standalone (not as part of the agent
# plugin package), so the package has to be brought in by hand. It is loaded by
# *spec* — deliberately NOT by putting the plugin directory on `sys.path`.
#
# Why: this plugin ships a top-level `tools.py`, and Hermes itself has a
# top-level `tools` package. With the plugin root on `sys.path`, every
# `import tools.*` inside the host resolved to this plugin's `tools.py` instead —
# `agent/gemini_schema.py` → `tools.schema_sanitizer` then died with
# "attempted relative import with no known parent package", which surfaced to
# the user as "Run failed: the model call failed". A plugin may never shadow a
# host module, so sys.path is left exactly as the host set it.
#
# The module name is derived from the install path, never hardcoded. A fixed
# name is how the pre-rename id (`upfront`) leaked back in: a leftover copy on
# disk — or a stale `upfront.models` already in `sys.modules` from an earlier
# load in the same process — answered for the new code, and the user saw
# "cannot import name 'ArtifactKind' from 'upfront.models'". Nothing here
# imports or registers that name any more, so no stale copy can be picked up.

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import re
import sys
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_PACKAGE_NAME = "_strategic_arena_dashboard_" + hashlib.sha256(
    str(_PLUGIN_ROOT).encode("utf-8")).hexdigest()[:16]
_SELF_FILE = Path(__file__).resolve()


def _same_package_files(mod) -> bool:
    """True when *mod* is this plugin's package (not one of its submodules)."""
    if mod is None:
        return False
    paths = getattr(mod, "__path__", None)
    if paths:
        try:
            return any(Path(p).resolve() == _PLUGIN_ROOT for p in paths)
        except OSError:
            return False
    filed = getattr(mod, "__file__", None)
    if filed:
        try:
            return Path(filed).resolve() == _PLUGIN_ROOT / "__init__.py"
        except OSError:
            return False
    return False


def _load_package():
    """Import the plugin package from this directory set without touching sys.path.

    Reuses the agent half when this process already imported it from the same
    files — the two halves then share one `llm_binding` holder, so the model the
    agent bound is the model the routes use. Otherwise loads a private copy under
    a name nothing else can collide with.
    """
    for _name, _mod in list(sys.modules.items()):
        if _name == _PACKAGE_NAME and _same_package_files(_mod):
            return _mod
    for _name, _mod in list(sys.modules.items()):
        if _mod is None or _mod is sys.modules.get(__name__):
            continue
        if _same_package_files(_mod):
            return _mod
    spec = importlib.util.spec_from_file_location(
        _PACKAGE_NAME, _PLUGIN_ROOT / "__init__.py",
        submodule_search_locations=[str(_PLUGIN_ROOT)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load the plugin package from {_PLUGIN_ROOT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_PACKAGE_NAME] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(_PACKAGE_NAME) is module:
            sys.modules.pop(_PACKAGE_NAME, None)
        raise
    return module


_PACKAGE = _load_package()
_PKG_NAME = _PACKAGE.__name__


def _sub(name: str):
    """Import a submodule of the plugin package, whichever name it was loaded under."""
    return importlib.import_module(f".{name}", _PKG_NAME)


engine = _sub("engine")
leverage = _sub("leverage")
llm_binding = _sub("llm_binding")
prices = _sub("prices")
reporting = _sub("reporting")
LlmAdapter = _sub("llm_adapter").LlmAdapter
_models = _sub("models")
Intervention = _models.Intervention

import os  # noqa: E402
import time  # noqa: E402

router = APIRouter()


def _debug(msg: str) -> None:
    """One line per model resolution, in the profile's data dir (survives updates).

    Cheap, and it turns "Run failed" into a diagnosis: whether the agent half was
    bound in *this* process, or whether we fell back to the local provider config.
    """
    try:
        path = _sub("paths").data_root() / "desktop-debug.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} pid={os.getpid()} {msg}\n")
    except Exception:
        pass


def set_llm(llm) -> None:
    """Bound by the agent plugin's register(ctx) — kept for compatibility.

    The binding itself lives in `llm_binding` (a process-wide holder)
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
        try:
            same_file = Path(getattr(_mod, "__file__", "") or "").resolve() == _SELF_FILE
        except OSError:
            same_file = False
        if same_file:
            _bound = getattr(_mod, "_LLM", None)
            if _bound is not None:
                return _bound, "agent-copy"

    try:
        # the host facade has no picked model to honour any more
        built = LlmAdapter(_sub("host_llm").build_host_llm())
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


def _copy_context_thread(fn):
    """Run *fn* on a worker thread inside THIS request's context.

    A bare ``threading.Thread`` starts with an empty context, so anything the
    host bound for the request — the profile secret scope above all — is gone by
    the time the run calls a model. That fails only for routes that resolve
    credentials through the secret scope (a picked model that has to be routed
    to a provider), which is why "run failed" showed up only for some models.
    Copying the context carries the binding across the thread boundary.
    """
    import contextvars

    ctx = contextvars.copy_context()

    def _runner():
        ctx.run(fn)

    return _runner


@router.get("/health")
async def health():
    try:
        _, source = _resolve_llm()
    except Exception as exc:
        return {"ok": False, "plugin": "strategic-arena", "llm_ready": False, "detail": str(exc)}
    return {"ok": True, "plugin": "strategic-arena", "llm_ready": True, "source": source}


@router.post("/run")
async def run(body: dict):
    """Start a review in a background thread. Returns {run_id} immediately."""
    try:
        scenario = _scenario_from(body)
    except HTTPException:
        raise
    except Exception as exc:
        # Name the folder that answered. When two copies of this plugin are
        # installed, the one that failed is the whole diagnosis — and it is not
        # the one the user is looking at.
        raise HTTPException(
            status_code=400,
            detail=(f"invalid scenario: {exc} — raised by the plugin at "
                    f"{_PLUGIN_ROOT} (package {_PKG_NAME})"))

    run_id = uuid.uuid4().hex[:12]
    engine._emit(run_id, "running", 0, scenario.rounds)

    def _work():
        try:
            def _on_round(snap):
                engine._emit(run_id, "running", snap.round, scenario.rounds,
                             {k: round(v, 3) for k, v in (snap.stances or {}).items()})
            # one adapter, the one this process bound: the session's model. No
            # per-run override is built here, because there is no picker to honour.
            llm = _llm()
            result = engine.run_scenario_progress(
                scenario, llm, on_round=_on_round, run_id=run_id
            )
            # the host can still substitute a model on its own; when it does, say
            # so next to the run instead of letting the report imply otherwise
            note = getattr(llm, "fallback_note", "") or ""
            if note:
                try:
                    (reporting.runs_dir() / run_id / "model-note.txt").write_text(note)
                except Exception:
                    pass
            # the host reported real token usage and its own cost estimate per
            # call; that sum is the only honest "what this run cost" number.
            try:
                usage = dict(getattr(llm, "usage", None) or {})
                if usage:
                    (reporting.runs_dir() / run_id / "usage.json").write_text(
                        json.dumps(usage))
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

    threading.Thread(target=_copy_context_thread(_work), daemon=True).start()
    return {"run_id": run_id, "status": "running"}


@router.get("/status/{run_id}")
async def status(run_id: str):
    run_id = _checked_run_id(run_id)
    prog = dict(engine.get_progress(run_id))
    # What each party is worth, live. Arithmetic only — measured 0.5ms for a
    # 5-party room against 1-2 minutes of model time per round, so there is no
    # reason to hide the ledger until the room closes.
    try:
        run = reporting.load_run(run_id)
        if (run.get("meta") or {}).get("personas"):
            prog["leverage"] = leverage.ledger_for_run(run)
        else:
            live = prog.get("stances") or {}
            prog["leverage"] = leverage.ledger([
                {"name": n, "stance": s, "capacity": 0.5} for n, s in live.items()
            ]) if live else {"available": False, "why": "the room has not been read yet"}
            prog["leverage"]["live"] = True
            prog["leverage"]["why"] = (
                "live estimate — capacity is assumed (0.5) until the room closes and "
                "each party's standing to stop you is assessed")
    except Exception as exc:
        prog["leverage"] = {"available": False, "why": f"could not be computed: {exc}"}
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
    GraphStore = _sub("graph").GraphStore
    graph_path = _sub("paths").graph_path
    return GraphStore(graph_path()).as_payload()


@router.get("/report/{run_id}")
async def report(run_id: str, full: bool = False):
    run_id = _checked_run_id(run_id)
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
    usage: dict = {}
    try:
        usage = json.loads((reporting.runs_dir() / run_id / "usage.json").read_text())
    except Exception:
        pass
    return {
        "report": data[key], "full": full, "model_note": model_note,
        "model_requested": meta.get("model_requested") or meta.get("model") or "",
        "model_served": meta.get("model_served") or "",
        "model_served_provider": meta.get("model_served_provider") or "",
        "model_fallback_note": meta.get("model_fallback_note") or "",
        "usage": usage,
        "recommendation": meta.get("recommendation") or "",
        "summary": meta.get("summary") or "",
        "kind": meta.get("kind") or "",
        "read": meta.get("read") or {},
        "moat": meta.get("moat") or {},
        "blocker": meta.get("blocker"),
        "blocker_stance": meta.get("blocker_stance"),
        "blocker_capacity": meta.get("blocker_capacity"),
        "counter_moves": meta.get("counter_moves") or [],
        "personas": meta.get("personas") or [],
        "interventions": meta.get("interventions") or [],
        "camps": meta.get("camps") or [],
    }


@router.get("/events/{run_id}")
async def events(run_id: str):
    """The round-by-round transcript — what each party actually said."""
    try:
        return {"events": reporting.load_events(run_id),
                "snapshots": reporting.load_snapshots(run_id)}
    except Exception:
        return {"events": [], "snapshots": []}


@router.get("/claims/{run_id}")
async def claims(run_id: str):
    return {"claims": reporting.load_claims(run_id)}


@router.get("/leverage/{run_id}")
async def leverage_route(run_id: str):
    """What each party is worth — computed from the room's own friction function.

    Read-only, deterministic, no model call: reopening a run must return the same
    numbers it returned the first time, which is why this is arithmetic and not a
    second opinion from an LLM.
    """
    try:
        return leverage.ledger_for_run(reporting.load_run(run_id))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"no run {run_id}")


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


# ── desktop UI build tracking ─────────────────────────────────────────

_BUILD_RE = re.compile(r"^\s*const\s+BUILD\s*=\s*'([^']*)'", re.M)
PLUGIN_NAME = "strategic-arena"


def _read_build(path: Path) -> str:
    """The BUILD constant inside a desktop plugin.js, or '' when unreadable."""
    try:
        match = _BUILD_RE.search(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return ""
    return (match.group(1).strip() if match else "")


def _published_path() -> Path | None:
    """Where the app actually loads this plugin's UI from (the app-level root).

    The app-level root is ``<hermes home>/desktop-plugins/``; the app copies a
    unified package's ``desktop/`` half there and refreshes it on its plugin
    scan. Only the public ``hermes_constants`` root is used — a plugin must not
    reach into host internals to write that folder.
    """
    try:
        from hermes_constants import get_default_hermes_root

        return get_default_hermes_root() / "desktop-plugins" / PLUGIN_NAME / "plugin.js"
    except Exception:
        return None


def _ui_status(running: str) -> dict:
    source = _read_build(_PLUGIN_ROOT / "desktop" / "plugin.js")
    published = ""
    try:
        pub = _published_path()
        published = _read_build(pub) if pub else ""
    except Exception:
        pass
    up_to_date = bool(source) and running == source
    published_current = bool(published) and published == source
    return {
        "running": running,
        "installed": source,
        "published": published,
        "up_to_date": up_to_date,
        "published_current": published_current,
        # Never say "reload the page" as if that were the fix: the file this
        # window runs is on the machine the app runs on, which a page reload
        # cannot reach. Say what to do instead.
        "hint": ("" if up_to_date else
                 f"This window is running build {running or 'unknown'}; build "
                 f"{source or 'unknown'} is installed. The app reads its UI from "
                 "the machine it runs on, so update it there — either Install from "
                 "Git with the Desktop target ticked, or save the new plugin.js "
                 "over the copy in desktop-plugins. Neither needs a restart."),
    }


@router.get("/ui")
async def ui_status(build: str = ""):
    """The build this window runs vs the build on disk, so a stale window says so.

    The app loads the desktop half from its own copy in `<hermes home>/desktop-plugins/`,
    which is refreshed on the app's plugin scan — so "I just updated the plugin" and
    "my window shows the new build" are two different things. The header asks this
    route instead of making the user guess.
    """
    return _ui_status(build)


@router.get("/price")
async def price(model: str = "", tin: int = 0, tout: int = 0):
    """The published price for one model id, and what those tokens would cost.

    Read-only by construction: this route cannot choose a model, hold a
    credential, or fail a run. When the catalogue does not carry the model (or is
    unreachable) it answers `found: false` and the form falls back to tokens —
    a made-up price would look like data, which is the one thing this product
    will not print.
    """
    try:
        hit = prices.price_for(model)
    except Exception as exc:
        return {"found": False, "model": model, "why": f"price lookup failed: {exc}"}
    if not hit:
        return {"found": False, "model": model,
                "why": "the Nous catalogue does not publish a price for this model"}
    cost = None
    if tin or tout:
        cost = round((max(0, tin) / 1_000_000) * hit["prompt_per_m"]
                     + (max(0, tout) / 1_000_000) * hit["completion_per_m"], 4)
    return {"found": True, "model": model, "matched": hit.get("id", ""),
            "prompt_per_m": hit["prompt_per_m"], "completion_per_m": hit["completion_per_m"],
            "free": hit["free"], "cost_usd": cost}


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

    The desktop and `arena_due` both read this — one payload, one truth.
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

def _checked_run_id(run_id: str) -> str:
    """Reject a run_id that is not the format this plugin mints, before it reaches a path.

    `reporting` validates inside `_run_dir`, but `status` and `report` read
    `meta.json` / `model-note.txt` / `usage.json` beside the run directory
    directly, so they need the same guard at the door.
    """
    try:
        return reporting.validate_run_id(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _scenario_from(body: dict):
    models = _sub("models")
    Document, Persona, Scenario = models.Document, models.Persona, models.Scenario
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
        # The lens. This was dropped on the floor: the chooser sent `kind`, the
        # route never read it, so every run silently fell back to auto-detect and
        # an explicitly chosen room could never be honoured. Validated here so an
        # unknown value is a 400 and not a quiet change of room.
        kind=_kind_or_auto(body.get("kind")),
    )


def _kind_or_auto(value) -> str:
    try:
        ArtifactKind = _sub("models").ArtifactKind
    except Exception as exc:
        # The one way this import fails is a broken install: the backend file is
        # not the one beside it on disk. A raw ImportError in a 400 tells the
        # reader nothing they can act on, so name the fix instead.
        raise HTTPException(
            status_code=500,
            detail=(
                "This Strategic Arena install is broken: its own engine modules "
                "could not be loaded from the plugin folder. That happens when the "
                "plugin was only partly updated, or an old copy is still installed "
                "beside it. Fix: in the app's Plugins tab remove Strategic Arena "
                "(and any leftover 'upfront' entry), then install it again from a "
                "single clean copy. Underlying error: " + str(exc)))
    try:
        return ArtifactKind(str(value or "auto")).value
    except ValueError:
        raise HTTPException(status_code=400,
                            detail=f"unknown kind {value!r}; expected one of "
                                   + ", ".join(k.value for k in ArtifactKind))
