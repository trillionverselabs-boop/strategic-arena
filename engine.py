# Engine — orchestrates a full run: ingest -> graph -> simulate -> score -> persist.

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable, Dict, List

from . import ingestion, reporting, scoring, simulation
from .fetch import fetch_urls
from .graph import GraphStore
from .models import Persona, Scenario, SimulationResult

GRAPH_PATH = Path.home() / ".hermes" / "upfront" / "graph.json"

# in-memory progress registry for the desktop poll/socket
_LOCK = threading.Lock()
_PROGRESS: Dict[str, dict] = {}   # run_id -> {status, round, total, snapshot_stances}
_RESULTS: Dict[str, SimulationResult] = {}


def _emit(run_id: str, status: str, round_: int = 0, total: int = 0, stances: dict | None = None):
    with _LOCK:
        _PROGRESS[run_id] = {
            "status": status, "round": round_, "total": total,
            "progress": round((round_ / total) * 100) if total else 0,
            "stances": stances or {},
        }


def run_scenario(scenario: Scenario, llm) -> SimulationResult:
    """Blocking full run. Used by the tool/CLI paths."""
    result = run_scenario_progress(scenario, llm)
    return result


def run_scenario_progress(scenario: Scenario, llm, on_round: Callable | None = None) -> SimulationResult:
    _emit(scenario.title, "running", 0, scenario.rounds)  # keyed by run id later

    # 0. URLs -> documents (so a user can drop a repo/post URL instead of pasting)
    if scenario.urls:
        scenario.documents = list(scenario.documents) + fetch_urls(scenario.urls)

    if not scenario.documents:
        raise ValueError("Provide at least one document or URL.")

    # 1. personas: user-supplied, else extract
    personas: List[Persona] = list(scenario.personas)
    relationships = []
    if not personas:
        personas, relationships = ingestion.extract_personas(
            scenario.documents, llm, scenario.max_personas
        )
    if not personas:  # extraction failed / empty — graceful fallback
        personas = [Persona(name=f"Stakeholder {i+1}", stance=0.0) for i in range(3)]

    # 2. graph (fresh per run — stale nodes from earlier runs are cleared out)
    graph = GraphStore(GRAPH_PATH)
    graph.clear()
    for p in personas:
        graph.add_node(p.name, name=p.name, kind="persona", stance=round(p.stance, 3),
                       role=p.role, reasons=p.reasons)
    for a, b, lbl in relationships:
        graph.add_edge(a, b, lbl)
    # link personas that oppose each other by stance sign (derived edges if none from LLM)
    if not relationships:
        ppl = sorted(personas, key=lambda p: p.stance)
        if len(ppl) >= 2:
            graph.add_edge(ppl[0].name, ppl[-1].name, "opposes")

    # 3. grounding: input quality -> confidence
    quality, confidence, suggestions = scoring.score_input(scenario.documents)

    # 4. simulate
    def _cb(snap):
        # emit live stances each round so /status carries a snapshot the desktop
        # can render as an updating graph (the just-finished round's stances)
        _emit(scenario.title, "running", snap.round, scenario.rounds,
              {k: round(v, 3) for k, v in (snap.stances or {}).items()})
        if on_round:
            on_round(snap)

    result = simulation.run_simulation(scenario, personas, on_round=_cb, llm=llm)
    # refresh graph stances after sim
    for p in result.personas:
        graph.add_node(p.name, name=p.name, kind="persona", stance=round(p.stance, 3),
                       role=p.role, reasons=p.reasons)
    graph.save()

    # 5. score
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
    # provenance for the report
    prov = []
    for p in result.personas:
        if p.reasons and p.reasons[0]:
            prov.append(f"{p.name} stance {p.stance:+.2f} — {p.reasons[0]}")
    result.provenance = prov

    # 6. persist (history + frozen log + report + opt-in full report)
    report_md = reporting.write_report(result)
    full_md = reporting.write_full_report(result)
    frozen = reporting.write_frozen_log(result)
    reporting.save_run(result, report_md, frozen, graph.as_payload(result.camps), full_md)

    with _LOCK:
        _RESULTS[result.run_id] = result
    _emit(result.run_id, "done", result.rounds, result.rounds, {p.name: round(p.stance, 3) for p in result.personas})
    return result


# ── progress inspection (for /status) ────────────────────────────────

def get_progress(run_id: str) -> dict:
    with _LOCK:
        return _PROGRESS.get(run_id, {"status": "unknown", "progress": 0})


def get_result(run_id: str) -> SimulationResult | None:
    with _LOCK:
        return _RESULTS.get(run_id)
