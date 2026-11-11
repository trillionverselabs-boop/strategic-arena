"""The round transcript and the movement series are the product's warmth.

A result page that only shows final positions reads like a lab printout. These
tests pin the two things that make it a story instead: the run's own frozen
statements, and the per-round stance series they can be replayed against.
"""

from pathlib import Path

from upfront import agents, engine, reporting
from upfront.models import Document, DocumentType, Scenario
from fakes import FakeLLM


def _run(window="30m"):
    sc = Scenario(title=f"events-{window}", window=window,
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    return engine.run_scenario(sc, FakeLLM())


def test_a_round_carries_what_was_said():
    """Snapshot.events is what the live view reads out loud; without it a
    watcher sees a dot move and nothing to read."""
    res = _run()
    assert res.snapshots, "a run must publish a snapshot per round"
    assert all(hasattr(s, "events") for s in res.snapshots)


def test_events_route_serves_the_frozen_log():
    import importlib.util
    from pathlib import Path

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    res = _run()

    path = Path(__file__).resolve().parent.parent / "dashboard" / "plugin_api.py"
    spec = importlib.util.spec_from_file_location("upfront_dashboard_events_api", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    app = FastAPI()
    app.include_router(mod.router, prefix="/api/plugins/strategic-arena")
    body = TestClient(app).get(f"/api/plugins/strategic-arena/events/{res.run_id}").json()

    assert "events" in body and "snapshots" in body
    assert len(body["events"]) == len(res.events)
    assert len(body["snapshots"]) == len(res.snapshots)
    assert all(set(e) >= {"round", "actor", "action", "text"} for e in body["events"])
    assert all(set(s) >= {"round", "stances"} for s in body["snapshots"])


def test_parties_speak_in_their_own_voice():
    """The old prompt produced 'Finance blocks ... so Finance blocks pending
    cost controls' — reportage, not a person. The instruction has to stay."""
    src = (Path(__file__).resolve().parent.parent / "agents.py").read_text()
    assert "first person" in src
    assert "third person" in src
    assert agents.StakeholderAgent is not None


def test_movement_series_comes_from_the_saved_log():
    """Nothing is reconstructed after the fact: the chart reads the same frozen
    JSONL the claims were written to."""
    res = _run()
    snaps = reporting.load_snapshots(res.run_id)
    assert snaps
    assert sorted(s["round"] for s in snaps) == sorted(s.round for s in res.snapshots)
    for s in snaps:
        assert s["stances"]
