"""A run_id reaches a filesystem path; it must be the format we mint.

`reporting._run_dir` joined the id as-is, so `../` walked out of `runs/` and
`mark_verified` would rewrite an existing `meta.json` anywhere the user can
write. Every reporting entry point goes through `_run_dir`, so one guard there
covers them all.
"""

import pytest

from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario
from fakes import FakeLLM


def _run():
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    return engine.run_scenario(sc, FakeLLM())


@pytest.mark.parametrize("bad", ["../evil", "..", "ABC", "0" * 11, "0" * 13,
                                 "g" * 12, "", "1234567890ab/../../etc"])
def test_a_run_id_that_is_not_the_minted_format_is_refused(bad):
    with pytest.raises(ValueError):
        reporting.load_run(bad)


@pytest.mark.parametrize("good", ["0123456789ab", "a" * 12, "deadbeef0000"])
def test_the_minted_format_is_accepted(good):
    assert reporting.validate_run_id(good) == good


def test_a_minted_run_id_still_loads():
    res = _run()
    assert reporting.load_run(res.run_id)["meta"]["run_id"] == res.run_id


def test_mark_verified_cannot_rewrite_a_file_outside_runs(tmp_hermes_home):
    """The exact attack: a pre-existing meta.json outside runs/ must be untouched."""
    outside = reporting.runs_dir().parent / "meta.json"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text('{"victim": true}')
    with pytest.raises(ValueError):
        reporting.mark_verified("..", "right")
    assert outside.read_text() == '{"victim": true}'


def test_the_agent_tools_return_an_error_for_a_malformed_run_id():
    import json as _json
    from upfront.tools import register_tools

    class Ctx:
        def __init__(self):
            self.handlers = {}

        def register_tool(self, name, toolset, schema, handler):
            self.handlers[name] = handler

    c = Ctx()
    register_tools(c)
    out = _json.loads(c.handlers["arena_report"]({"run_id": "../evil"}))
    assert "error" in out and "run_id" in out
    out = _json.loads(c.handlers["arena_export"]({"run_id": "../evil"}))
    assert "error" in out and "run_id" in out


def test_the_routes_reject_a_malformed_run_id():
    import importlib.util
    from pathlib import Path

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    path = Path(__file__).resolve().parent.parent / "dashboard" / "plugin_api.py"
    spec = importlib.util.spec_from_file_location("upfront_dashboard_run_id_guard", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    app = FastAPI()
    app.include_router(mod.router, prefix="/api/plugins/strategic-arena")
    client = TestClient(app)
    assert client.get("/api/plugins/strategic-arena/status/not-a-run-id").status_code == 400
    assert client.get("/api/plugins/strategic-arena/report/not-a-run-id").status_code == 400
