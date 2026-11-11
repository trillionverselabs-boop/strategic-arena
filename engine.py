# Engine — orchestrates a full run: ingest -> manifest -> graph -> simulate -> score
# -> claims -> persist. A run either produces a grounded result or raises loudly.

from __future__ import annotations

import json
import threading
from typing import Callable, Dict, List

from . import ingestion, moat as moat_mod, reporting, scoring, simulation
from .claims import build_claims, extract_claims
from . import fetch
from .fetch import fetch_urls
from .graph import GraphStore
from .manifest import build_manifest
from .models import (
    ArtefactKind,
    Document,
    DocumentType,
    Intervention,
    Persona,
    Scenario,
    SimulationResult,
)
from .paths import graph_path


class SimulationError(RuntimeError):
    """A run that cannot produce a trustworthy result. Surfaced to the user as-is."""


# in-memory progress / results / injection queues for the desktop
_LOCK = threading.Lock()
_PROGRESS: Dict[str, dict] = {}
_RESULTS: Dict[str, SimulationResult] = {}
_INJECT: Dict[str, list] = {}
_CANCEL: Dict[str, bool] = {}


class SimulationCancelled(RuntimeError):
    """The user stopped the run. Not an error — nothing is written to history."""


def _norm(model_id: str) -> str:
    """Canonical form for comparing a requested model with the served one."""
    text = (model_id or "").strip().lower().lstrip("~")
    for suffix in (":batch", ":us"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
    return text


def _vendor(model_id: str) -> str:
    """``deepseek/x`` -> ``deepseek``. Empty when the id has no vendor prefix."""
    text = _norm(model_id)
    return text.split("/", 1)[0] if "/" in text else ""


def _same_model_family(requested: str, served: str) -> bool:
    """True when *served* is the requested model, or its concrete form.

    ``~deepseek/deepseek-flash-latest`` is the catalogue's "latest" alias: the host
    resolves it to a concrete DeepSeek build (``deepseek/deepseek-v4.1-flash-1017``)
    and reports that. That is the pick working, not a substitution, so the vendor
    decides. A vendor mismatch — or a requested id with no vendor at all — falls
    back to a full-string compare, which is what catches a model the host could not
    serve and quietly replaced with the active one.
    """
    req_vendor, srv_vendor = _vendor(requested), _vendor(served)
    if req_vendor and srv_vendor:
        return req_vendor == srv_vendor
    return _norm(requested) == _norm(served)


def _emit(run_key: str, status: str, round_: int = 0, total: int = 0,
          stances: dict | None = None, events: list | None = None) -> None:
    """Publish one progress tick.

    `events` is the round that just closed: the live view reads these out loud,
    because a moving dot is not a story and a 48h run has to be watchable.
    """
    with _LOCK:
        prev = _PROGRESS.get(run_key) or {}
        before = prev.get("stances") or {}
        now = stances or {}
        movers = []
        if before and now:
            for k, v in now.items():
                if k in before:
                    d = round(v - before[k], 3)
                    if abs(d) >= 0.05:
                        movers.append({"name": k, "delta": d})
            movers.sort(key=lambda m: abs(m["delta"]), reverse=True)
        _PROGRESS[run_key] = {
            "status": status, "round": round_, "total": total,
            "progress": round((round_ / total) * 100) if total else 0,
            "stances": now,
            "events": events or prev.get("events") or [],
            "previous": before if before else None,
            "movers": movers[:5],
        }


def cancel(run_id: str) -> bool:
    """Ask a live run to stop at the next round boundary. False when not running."""
    with _LOCK:
        prog = _PROGRESS.get(run_id)
        if prog is None or prog.get("status") not in ("running",):
            return False
        _CANCEL[run_id] = True
        return True


def _cancelled(run_id: str) -> bool:
    return bool(_CANCEL.get(run_id))


def inject(run_id: str, intervention: Intervention) -> bool:
    """Queue a mid-run intervention. False when the run is not live."""
    with _LOCK:
        queue = _INJECT.get(run_id)
        if queue is None:
            return False
        queue.append(intervention)
        return True


def run_scenario(scenario: Scenario, llm) -> SimulationResult:
    """Blocking full run. Used by the tool/CLI paths."""
    return run_scenario_progress(scenario, llm)


def run_scenario_progress(scenario: Scenario, llm, on_round: Callable | None = None,
                          run_id: str | None = None) -> SimulationResult:
    key = run_id or scenario.title
    _emit(key, "running", 0, scenario.rounds)

    # 0. URLs -> documents (so a user can drop a repo/post URL instead of pasting)
    skipped: List[tuple] = []
    if scenario.urls:
        scenario.documents = list(scenario.documents) + fetch_urls(scenario.urls)
        skipped = list(fetch.LAST_SKIPPED)

    if not scenario.documents:
        raise SimulationError("Provide at least one document or URL.")

    # 1. personas: user-supplied, else extract — never invent
    personas: List[Persona] = list(scenario.personas)
    relationships: List[tuple] = []
    # the lens: what was handed in decides who could possibly react
    kind = scenario.kind.value if scenario.kind.value != "auto" else ingestion.detect_kind(
        scenario.urls, scenario.documents[0].content if scenario.documents else "")
    # 1a. A research paper gets its moat decoded BEFORE the room is drawn, so the
    # stakeholders argue about a product with a clock on it rather than about a
    # citation. The decode goes back in as a context document on purpose: every
    # party in this room has read the same public paper, and that is the point.
    moat = None
    if kind == ArtefactKind.PAPER.value:
        moat = moat_mod.decode(scenario.documents, llm)
        if not moat.error and moat.product:
            scenario.documents = list(scenario.documents) + [
                Document(type=DocumentType.CONTEXT, content=moat.brief(),
                         source="moat decode")]

    if not personas:
        extracted = ingestion.extract_personas(
            scenario.documents, llm, scenario.max_personas, kind=kind
        )
        if extracted is None:
            detail = ingestion.LAST_ERROR or "no error detail was recorded"
            raise SimulationError(
                "The model call failed, so no stakeholders could be read from your "
                f"documents. Nothing was simulated. Underlying error: {detail}"
            )
        personas, relationships = extracted
        if not personas:
            raise SimulationError(
                "The model read your documents but found no stakeholders in them. "
                "Add a decision document that names who is affected, or supply personas."
            )

    # 2. replication manifest — how this run was made
    manifest = build_manifest(
        scenario, scenario.documents,
        getattr(llm, "model", "default"), getattr(llm, "temperature", 0.6),
    )

    # 3. graph (fresh per run)
    graph = GraphStore(graph_path())
    graph.clear()
    for p in personas:
        graph.add_node(p.name, name=p.name, kind="persona", stance=round(p.stance, 3),
                       capacity=p.capacity, role=p.role, reasons=p.reasons)
    for a, b, lbl in relationships:
        graph.add_edge(a, b, lbl)
    if not relationships:
        ppl = sorted(personas, key=lambda p: p.stance)
        if len(ppl) >= 2:
            graph.add_edge(ppl[0].name, ppl[-1].name, "opposes")

    # 4. grounding: input quality -> confidence
    quality, confidence, suggestions = scoring.score_input(scenario.documents)

    # 5. simulate (draining any mid-run injections)
    def _cb(snap):
        _emit(key, "running", snap.round, scenario.rounds,
              {k: round(v, 3) for k, v in (snap.stances or {}).items()},
              [ev.model_dump() if hasattr(ev, "model_dump") else ev
               for ev in (getattr(snap, "events", None) or [])])
        if on_round:
            on_round(snap)

    _INJECT[key] = []
    try:
        # a cancel is honoured between rounds: the current round finishes, then
        # the run stops. Nothing partial is ever written to history.
        def _check_cancel(snap):
            _cb(snap)
            if _cancelled(key):
                raise SimulationCancelled("cancelled by the user")

        result = simulation.run_simulation(
            scenario, personas, on_round=_check_cancel, llm=llm,
            injection_queue=_INJECT[key],
        )
    except SimulationCancelled:
        _emit(key, "cancelled", 0, scenario.rounds)
        raise
    finally:
        _INJECT.pop(key, None)
        _CANCEL.pop(key, None)

    if run_id:
        result.run_id = run_id
    result.window = scenario.window.value
    result.kind = result.kind or kind
    if moat is not None and (moat.error or moat.product):
        # recorded even when it FAILED: an absent card must not read as "no moat",
        # so a failed decode says so in one line instead of vanishing
        result.moat = moat.model_dump()
    if not result.read:
        result.read = dict(ingestion.LAST_READ)

    for p in result.personas:
        graph.add_node(p.name, name=p.name, kind="persona", stance=round(p.stance, 3),
                       capacity=p.capacity, role=p.role, reasons=p.reasons)
    graph.save()

    # 6. score + read the landscape
    friction, uncertainty = scoring.friction_score(result, quality)
    result.friction = friction
    result.uncertainty = uncertainty
    result.confidence = confidence
    result.blocker = scoring.find_blocker(result.personas)
    result.counter_moves = scoring.build_counter_moves(result.blocker, result)

    from .camps import cluster_camps
    from .failure_modes import evaluate_run as evaluate_failure_modes
    from .recommendations import build_recommendation

    result.camps = cluster_camps(result.personas, relationships)
    result.failure_modes = evaluate_failure_modes(result)
    result.recommendation = build_recommendation(result)
    result.input_quality = {"quality": quality, "documents": len(scenario.documents),
                            "suggestions": suggestions}
    result.sea = scoring.sea_state(result)
    result.claims = build_claims(result)

    # 7. degradation must be visible, never silent
    result.served_model = getattr(llm, "served_model", "") or ""
    result.served_provider = getattr(llm, "served_provider", "") or ""
    result.model_fallback_note = getattr(llm, "fallback_note", "") or ""
    # The host does NOT raise when it cannot serve the picked model: it routes
    # the call to whatever is active and reports that model back. So the only
    # honest check is requested-vs-served, done here rather than trusted to an
    # exception that never comes.
    requested = (getattr(llm, "model", "") or "").strip()
    served = (result.served_model or "").strip()
    if requested and requested != "default" and served and not _same_model_family(requested, served):
        if not result.model_fallback_note:
            result.model_fallback_note = (
                f"You picked {requested}, but this run was served by {served} "
                f"({result.served_provider or 'unknown provider'}). The host routes an "
                "unusable model to your active model instead of refusing it."
            )
    total_calls = max(1, scenario.rounds * max(1, len(result.personas)))
    if result.llm_failures:
        result.degraded = True
        result.degraded_reason = (
            f"{result.llm_failures} of {total_calls} model calls failed during the run"
        )
        result.confidence = "low"

    # 8. provenance for the report
    prov = []
    # A link that could not be read is a fact about the run, not a detail to
    # swallow: reviewing two documents when three were handed in is a silent
    # downgrade, and the reader is the last person who can be told.
    for url, why in skipped:
        prov.append(f"SKIPPED {url} — {why}")
    for p in result.personas:
        if p.reasons and p.reasons[0]:
            prov.append(f"{p.name} stance {p.stance:+.2f} — {p.reasons[0]}")
    result.provenance = prov

    # 9. optional GraphRAG claim enrichment (never required, never fatal)
    extra = extract_claims(result, llm, scenario.documents)
    if extra:
        result.claims = result.claims + extra

    # 10. persist (history + frozen log + report + opt-in full report)
    report_md = reporting.write_report(result)
    full_md = reporting.write_full_report(result)
    frozen = reporting.write_frozen_log(result, manifest=manifest)
    manifest["model_requested"] = getattr(llm, "model", "") or ""
    manifest["model_served"] = result.served_model
    manifest["model_served_provider"] = result.served_provider
    reporting.save_run(result, report_md, frozen, graph.as_payload(result.camps),
                       full_md, manifest=manifest)

    with _LOCK:
        _RESULTS[result.run_id] = result
    _emit(result.run_id, "done", result.rounds, result.rounds,
          {p.name: round(p.stance, 3) for p in result.personas})
    return result


def run_pair(scenario: Scenario, llm, intervention: Intervention,
             run_id_baseline: str, run_id_treatment: str) -> dict:
    """Baseline vs treatment: same documents, one variable changed (counterfactual)."""
    baseline = run_scenario_progress(scenario, llm, run_id=run_id_baseline)

    treated = scenario.model_copy(deep=True)
    treated.interventions = [intervention]
    treatment = run_scenario_progress(treated, llm, run_id=run_id_treatment)

    def _stances(res):
        return {p.name: round(p.stance, 3) for p in res.personas}

    b, t = _stances(baseline), _stances(treatment)
    pair = {
        "baseline_run": baseline.run_id,
        "treatment_run": treatment.run_id,
        "intervention": {"name": intervention.name, "description": intervention.description},
        "friction_delta": round(treatment.friction - baseline.friction, 1),
        "stance_delta": {k: round(t[k] - b.get(k, 0.0), 3) for k in t},
        "verdict": ("counter-move works" if treatment.friction < baseline.friction
                    else "counter-move did not help"),
    }
    (reporting.runs_dir() / baseline.run_id / "pair.json").write_text(json.dumps(pair, indent=1))
    return pair


# ── progress inspection (for /status) ────────────────────────────────

def get_progress(run_id: str) -> dict:
    with _LOCK:
        return _PROGRESS.get(run_id, {"status": "unknown", "progress": 0})


def get_result(run_id: str) -> SimulationResult | None:
    with _LOCK:
        return _RESULTS.get(run_id)
