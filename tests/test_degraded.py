from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario
from fakes import HalfDead


def test_degraded_run_is_flagged():
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Ship it")])
    res = engine.run_scenario(sc, HalfDead())
    assert res.degraded is True
    assert res.confidence == "low"
    assert "DEGRADED RUN" in reporting.load_run(res.run_id)["report"]
