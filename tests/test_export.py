"""R3 — the decision record: the review as a file next to the code.

The retention hook. If the review is a file in the repo, it gets re-read, linked from PRs, and
compared against reality by the people who ship.
"""

from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario
from tests.fakes import FakeLLM


def _run(title="Ship the open-weight release"):
    sc = Scenario(title=title, window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    return engine.run_scenario(sc, FakeLLM())


def test_export_writes_a_decision_file():
    res = _run()
    path = reporting.export_decision(res.run_id)
    assert path.endswith(".md")
    text = open(path).read()

    assert text.startswith("# Decision: Ship the open-weight release")
    assert f"- run: {res.run_id}" in text
    assert "competition:" in text and str(res.sea["label"]) in text
    assert f"friction: {res.friction:.0f}/100" in text
    assert f"veto player: {res.blocker.name}" in text
    for claim in res.claims:
        assert f"`{claim['id']}`" in text, "every claim must be listed with its id"
    assert "_unscored_" in text


def test_export_into_a_custom_dir():
    res = _run()
    path = reporting.export_decision(res.run_id, out_dir="decisions/2026-11")
    assert "decisions/2026-11" in path


def test_reexport_after_verify_fills_verdict_without_duplicating():
    res = _run()
    first = reporting.export_decision(res.run_id)
    hits = {c["id"]: (i % 2 == 0) for i, c in enumerate(res.claims)}
    reporting.mark_verified(res.run_id, "partial", "Eng blocked, one week later",
                            hits=hits, actual_friction=55.0)
    second = reporting.export_decision(res.run_id)

    assert first == second, "re-export must rewrite the same file"
    text = open(second).read()
    assert "_unscored_" not in text
    assert "partial" in text
    assert "Eng blocked, one week later" in text
    assert "✓" in text and "✗" in text
    assert text.count("# Decision:") == 1, "no duplicated sections"


def test_export_of_unknown_run_fails_loudly():
    import pytest
    with pytest.raises(FileNotFoundError):
        reporting.export_decision("nope")


def test_export_tool_is_registered():
    from upfront.tools import register_tools

    class Ctx:
        def __init__(self):
            self.schemas = {}

        def register_tool(self, name, toolset, schema, handler):
            self.schemas[name] = schema

    c = Ctx()
    register_tools(c)
    assert "upfront_export" in c.schemas
