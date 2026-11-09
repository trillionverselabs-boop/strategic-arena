# Engine — orchestrates a full run: ingest -> manifest -> graph -> simulate -> score
# -> claims -> persist. A run either produces a grounded result or raises loudly.

from __future__ import annotations

import json
import threading
from typing import Callable, Dict, List

from . import ingestion, reporting, scoring, simulation
from .claims import build_claims, extract_claims
from .fetch import fetch_urls
from .graph import GraphStore
from .manifest import build_manifest
from .models import Intervention, Persona, Scenario, SimulationResult
from .paths import graph_path


class SimulationError(RuntimeError):
    """A run that cannot produce a trustworthy result. Surfaced to the user as-is."""


# in-memory progress / results / injection queues for the desktop
_LOCK = threading.Lock()
_PROGRESS: Dict[str, dict] = {}
_RESULTS: Dict[str, SimulationResult] = {}
_INJECT: Dict[str, list] = {}


def _emit(run_key: str, status: str, round_: int = 0, total: int = 0,
          stances: dict | None = None) -> None:
    with _LOCK:
        _PROGRESS[run_key] = {
            "status": status, "round": round_, "total": total,
            "progress": round((round_ / total) * 100) if total else 0,
            "stances": stances or {},
        }


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
    if scenario.urls:
        scenario.documents = list(scenario.documents) + fetch_urls(scenario.urls)

    if not scenario.documents:
        raise SimulationError("Provide at least one document or URL.")

    # 1. personas: user-supplied, else extract — never invent
    personas: List[Persona] = list(scenario.personas)
    relationships: List[tuple] = []
    if not personas:
        extracted = ingestion.extract_personas(
            scenario.documents, llm, scenario.max_personas
        )
        if extracted is None:
            raise SimulationError(
                "The model call failed, so no stakeholders could be read from your "
                "documents. Nothing was simulated — check the model is reachable and re-run."
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
                       role=p.role, reasons=p.reasons)
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
              {k: round(v, 3) for k, v in (snap.stances or {}).items()})
        if on_round:
            on_round(snap)

    _INJECT[key] = []
    try:
        result = simulation.run_simulation(
            scenario, personas, on_round=_cb, llm=llm,
            injection_queue=_INJECT[key],
        )
    finally:
        _INJECT.pop(key, None)

    if run_id:
        result.run_id = run_id

    for p in result.personas:
        graph.add_node(p.name, name=p.name, kind="persona", stance=round(p.stance, 3),
                       role=p.role, reasons=p.reasons)
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
    total_calls = max(1, scenario.rounds * max(1, len(result.personas)))
    if result.llm_failures:
        result.degraded = True
        result.degraded_reason = (
            f"{result.llm_failures} of {total_calls} model calls failed during the run"
        )
        result.confidence = "low"

    # 8. provenance for the report
    prov = []
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
