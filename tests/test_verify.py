import json
import pytest

from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario
from tests.fakes import FakeLLM


def _run():
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    return engine.run_scenario(sc, FakeLLM())


def test_verdict_is_persisted():
    res = _run()
    reporting.mark_verified(res.run_id, "right", "Eng did block in review")
    meta = json.loads((reporting.runs_dir() / res.run_id / "meta.json").read_text())
    assert meta["verified"]["verdict"] == "right"


def test_bad_verdict_rejected():
    with pytest.raises(ValueError):
        reporting.mark_verified("nope", "maybe")


def test_claims_are_scored():
    res = _run()
    out = reporting.mark_verified(res.run_id, "partial",
                                  hits={"a": True, "b": False}, actual_friction=61.0)
    assert out["score"] == 0.5
    assert out["actual_friction"] == 61.0
    assert out["friction_error"] == round(abs(61.0 - res.friction), 1)
