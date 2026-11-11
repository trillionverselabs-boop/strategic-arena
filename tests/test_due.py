"""R1 — auto-rescore: claims become a to-do the system owns.

A run is "due" when its window has closed and nobody has scored it yet.
"""

import json
from datetime import datetime, timedelta, timezone

from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario
from upfront.tools import register_tools
from tests.fakes import FakeLLM


def _run(window="30m"):
    sc = Scenario(title=f"due-{window}", window=window,
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    return engine.run_scenario(sc, FakeLLM())


def _age(run_id, minutes):
    """Rewrite created_at to N minutes ago, the way a real run would look later."""
    p = reporting.runs_dir() / run_id / "meta.json"
    meta = json.loads(p.read_text())
    meta["created_at"] = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
    p.write_text(json.dumps(meta, indent=1))
    return meta


def test_window_is_persisted_in_meta():
    res = _run("30m")
    meta = json.loads((reporting.runs_dir() / res.run_id / "meta.json").read_text())
    assert meta["window"] == "30m"


def test_closed_window_is_due():
    res = _run("30m")
    _age(res.run_id, 60)                     # window is 30m; it closed 30m ago
    due = reporting.due_claims()
    assert [d["run_id"] for d in due] == [res.run_id]
    row = due[0]
    assert row["title"] == "due-30m"
    assert set(row) >= {"run_id", "title", "due_at", "claims"}
    assert row["claims"], "a due run must carry its frozen claims to score"
    assert all("id" in c and "claim" in c for c in row["claims"])
    datetime.fromisoformat(row["due_at"])     # parseable ISO timestamp


def test_open_window_is_not_due():
    res = _run("48h")
    _age(res.run_id, 10)
    assert reporting.due_claims() == []


def test_scored_run_is_not_due():
    res = _run("30m")
    _age(res.run_id, 60)
    reporting.mark_verified(res.run_id, "right", "Eng did block")
    assert reporting.due_claims() == []


def test_as_of_is_respected():
    res = _run("30m")
    _age(res.run_id, 60)
    earlier = datetime.now(timezone.utc) - timedelta(minutes=90)
    assert reporting.due_claims(as_of=earlier) == []


def test_due_route_serves_the_same_payload():
    """GET /due is what the desktop and an agent both read."""
    import importlib.util
    from pathlib import Path

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    res = _run("30m")
    _age(res.run_id, 60)

    path = Path(__file__).resolve().parent.parent / "dashboard" / "plugin_api.py"
    spec = importlib.util.spec_from_file_location("upfront_dashboard_api", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    app = FastAPI()
    app.include_router(mod.router, prefix="/api/plugins/strategic-arena")
    body = TestClient(app).get("/api/plugins/strategic-arena/due").json()

    assert [r["run_id"] for r in body["due"]] == [res.run_id]
    assert body["count"] == 1


def test_register_registers_bundled_skills():
    """Skills ship inside the plugin and resolve as `strategic-arena:<name>`."""
    from upfront import register

    class Ctx:
        llm = None

        def __init__(self):
            self.skills = {}
            self.tools = {}

        def has_capability(self, _name):
            return False

        def register_tool(self, name, toolset, schema, handler):
            self.tools[name] = schema

        def register_skill(self, name, path):
            self.skills[name] = path

        def log(self, *_a):
            pass

    c = Ctx()
    register(c)
    assert "review" in c.skills
    assert c.skills["review"].name == "SKILL.md"
    assert "arena_due" in c.tools


def test_due_tool_is_registered():
    class Ctx:
        def __init__(self):
            self.schemas = {}

        def register_tool(self, name, toolset, schema, handler):
            self.schemas[name] = schema

    c = Ctx()
    register_tools(c)
    assert "arena_due" in c.schemas
    assert c.schemas["arena_due"]["parameters"]["type"] == "object"
