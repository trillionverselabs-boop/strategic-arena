from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario
from tests.fakes import FakeLLM


def test_ledger_aggregates_scored_runs():
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    a = engine.run_scenario(sc, FakeLLM())
    b = engine.run_scenario(sc, FakeLLM())
    reporting.mark_verified(a.run_id, "right", hits={"x": True, "y": True})
    reporting.mark_verified(b.run_id, "wrong", hits={"x": False, "y": True})
    led = reporting.calibration()
    assert led["runs"] == 2
    assert led["verified"] == 2
    assert led["claim_hit_rate"] == 0.75
    assert led["verdicts"]["right"] == 1
