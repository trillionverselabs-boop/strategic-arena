from upfront import engine, reporting
from upfront.models import Document, DocumentType, Scenario
from fakes import FakeLLM


def test_one_run_one_record():
    sc = Scenario(title="t", window="6h",
                  documents=[Document(type=DocumentType.DECISION, content="Open-weight it")])
    engine.run_scenario_progress(sc, FakeLLM(), run_id="abc123")
    runs = reporting.list_runs(10)
    assert len(runs) == 1
    assert runs[0]["run_id"] == "abc123"
    assert (reporting.runs_dir() / "abc123" / "report.md").exists()
